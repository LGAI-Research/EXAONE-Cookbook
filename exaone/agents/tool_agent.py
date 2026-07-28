"""
(en) Single ToolAgent: BaseAgent ReAct loop with merged tool registries and ThinkingRouter phases.

- enrich: tools on, gather context via qualified tool_agent_key.tool_name calls
- NextStepPlanner: catalog screen + per-turn progress (LLM JSON, ledger for duplicates/budget)
- finalize: tools off, JSON answer (ToolAgent answer / ToolAgent rag prompt)

(kr) 단일 ToolAgent입니다. 병합된 tool registry와 ThinkingRouter phase를 사용하는 BaseAgent ReAct 루프입니다.

- enrich: tool on, qualified tool_agent_key.tool_name 호출로 context 수집
- NextStepPlanner: catalog screen + 턴별 progress(LLM JSON, 중복/예산용 ledger)
- finalize: tool off, JSON 답변(ToolAgent answer / ToolAgent rag prompt)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Literal

from exaone.agents.base_agent import BaseAgent, AgentContext, AgentResult
from exaone.agents.events import AgentEvent
from exaone.agents.next_step_planner import (
    EnrichRunState,
    EnrichStopReason,
    NextStepPlanner,
    append_progress_tool_hint,
    wrap_tool_executor_with_ledger,
)
from exaone.agents.run_trace import (
    AgentRunPhase,
    LlmCallTrace,
    get_active_llm_trace,
    reset_active_llm_trace,
    set_active_llm_trace,
)
from exaone.agents.prompts import (
    DEFAULT_SYSTEM_PROMPT_RAG,
    DEFAULT_SYSTEM_PROMPT_TOOL,
    ENRICH_PHASE_APPENDIX,
    FINALIZE_PHASE_APPENDIX,
)
from exaone.agents.rag_tools import RAG_TOOL_AGENT_KEY, build_rag_tool_registry
from exaone.agents.thinking_router import (
    RouteDecision,
    RoutePhase,
    ThinkingRouter,
    append_router_tool_hints,
)
from exaone.agents.tool_agent_catalog import (
    ANSWER_TOOL_AGENT_KEY,
    DEFAULT_TOOL_AGENT_KEY,
    ToolAgentCatalog,
)
from exaone.llm import ExaoneClient, ExaoneGenerateOptions, ExaoneMessage
from exaone.observability import fields as obs_fields
from exaone.output import StructuredOutputPipeline
from exaone.tools import ToolRegistry

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ENRICH_TURNS = 8
_DEFAULT_MAX_TOOL_INVOCATIONS = 12

PHASE_PREFLIGHT = "preflight"
PHASE_ENRICH = "enrich"
PHASE_FINALIZE = "finalize"


@dataclass
class _EnrichSetup:
    messages: list[Any]
    options: ExaoneGenerateOptions
    router_response_format: dict[str, Any] | None
    user_query: str
    enrich_route_decision: RouteDecision | None
    route_plan: Any | None = None


def _finalize_system_prompt(answer_tool_agent_key: str, base_system_prompt: str) -> str:
    if answer_tool_agent_key == RAG_TOOL_AGENT_KEY:
        return DEFAULT_SYSTEM_PROMPT_RAG + FINALIZE_PHASE_APPENDIX
    if answer_tool_agent_key == ANSWER_TOOL_AGENT_KEY:
        return (
            base_system_prompt.split(ENRICH_PHASE_APPENDIX)[0].rstrip()
            + FINALIZE_PHASE_APPENDIX
        )
    return base_system_prompt + FINALIZE_PHASE_APPENDIX


class ToolAgent(BaseAgent):
    """
    (en) ToolAgent: enrich (tools) → NextStepPlanner progress gate → finalize (tools off).

    Multiple ToolAgent configurations (e.g. ToolAgent rag, ToolAgent tool) are
    registered as separate tool registries and merged via ToolAgentCatalog.
    Pass retrieval_strategy to register ToolAgent (rag) with rag.retrieve.

    (kr) ToolAgent입니다: enrich(tool on) → NextStepPlanner progress gate → finalize(tool off).

    여러 ToolAgent 구성(예: ToolAgent rag, ToolAgent tool)은 별도 tool registry로 등록되며
    ToolAgentCatalog로 병합됩니다. retrieval_strategy를 넘기면 ToolAgent(rag)에 rag.retrieve가 등록됩니다.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        *,
        tool_agent_registries: dict[str, ToolRegistry] | None = None,
        retrieval_strategy: Any = None,
        tools: list[dict[str, Any]] | None = None,
        tool_executor: Callable[[str, dict[str, Any]], Any] | None = None,
        system_prompt: str | None = None,
        additional_system_prompt: str | None = None,
        max_turns: int = 10,
        max_enrich_turns: int | None = None,
        max_tool_invocations: int = _DEFAULT_MAX_TOOL_INVOCATIONS,
        use_thinking_router: bool = True,
        use_next_step_planner: bool = True,
    ):
        registries = tool_agent_registries
        self._catalog = ToolAgentCatalog()
        if registries:
            for key, reg in registries.items():
                self._catalog.register_tool_agent(key, reg)
        if tool_registry is not None:
            self._catalog.register_tool_agent(DEFAULT_TOOL_AGENT_KEY, tool_registry)
        if tools is not None and tool_executor is not None:
            raise ValueError(
                "Pass tool_registry= instead of raw tools= + tool_executor= "
                "(use ToolAgentCatalog-qualified names via ToolRegistry)"
            )
        if retrieval_strategy is not None:
            self._catalog.register_tool_agent(
                RAG_TOOL_AGENT_KEY,
                build_rag_tool_registry(retrieval_strategy),
            )

        if not self._catalog.has_tools() and tool_registry is None and not registries:
            self._catalog.register_tool_agent(DEFAULT_TOOL_AGENT_KEY, ToolRegistry())

        base_system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT_TOOL
        extra_prompt = (additional_system_prompt or "").strip()
        if extra_prompt:
            base_system_prompt = f"{base_system_prompt.rstrip()}\n\n{extra_prompt}"
        self.system_prompt = base_system_prompt
        self.max_turns = max_turns
        self.max_enrich_turns = max_enrich_turns if max_enrich_turns is not None else min(
            max_turns, _DEFAULT_MAX_ENRICH_TURNS
        )
        self.max_tool_invocations = max(1, max_tool_invocations)
        self.use_thinking_router = use_thinking_router
        self.use_next_step_planner = use_next_step_planner
        self._thinking_router: ThinkingRouter | None = None
        self._thinking_router_llm: ExaoneClient | None = None
        self._thinking_router_model: str | None = None
        self._next_step_planner: NextStepPlanner | None = None
        self._next_step_planner_llm: ExaoneClient | None = None
        self._next_step_planner_model: str | None = None

    @property
    def catalog(self) -> ToolAgentCatalog:
        return self._catalog

    @property
    def tools(self) -> list[dict[str, Any]]:
        """(en) Merged qualified tool schemas (LLM-facing).

        (kr) 병합된 qualified tool schema 목록입니다(LLM에 노출).
        """
        return self._catalog.get_merged_schemas()

    def tool_executor(self, name: str, arguments: dict[str, Any]) -> Any:
        return self._catalog.dispatch(name, arguments)

    def _get_thinking_router(self, llm: ExaoneClient) -> ThinkingRouter:
        model_name = getattr(llm, "model", ExaoneClient.DEFAULT_MODEL)
        if (
            self._thinking_router is None
            or self._thinking_router_llm is not llm
            or self._thinking_router_model != model_name
        ):
            self._thinking_router = ThinkingRouter(llm, model_name)
            self._thinking_router_llm = llm
            self._thinking_router_model = model_name
        return self._thinking_router

    @staticmethod
    def _attach_llm_calls_metadata(result: AgentResult) -> AgentResult:
        trace = get_active_llm_trace()
        if trace is not None and trace.records:
            meta = dict(result.metadata or {})
            meta[obs_fields.LLM_CALLS] = trace.to_metadata_list()
            result.metadata = meta
        return result

    @staticmethod
    def _should_run_catalog_screen_llm(
        planner: NextStepPlanner | None,
        router: ThinkingRouter | None,
    ) -> bool:
        """Run screen_catalog LLM only when Planner is on without Router enrich planning."""
        return planner is not None and router is None

    @staticmethod
    def _phase_event(
        event_type: Literal["phase_start", "phase_end"],
        phase: str,
        **payload: Any,
    ) -> AgentEvent:
        return AgentEvent(type=event_type, payload={"phase": phase, **payload})

    def _get_next_step_planner(self, llm: ExaoneClient) -> NextStepPlanner:
        model_name = getattr(llm, "model", ExaoneClient.DEFAULT_MODEL)
        if (
            self._next_step_planner is None
            or self._next_step_planner_llm is not llm
            or self._next_step_planner_model != model_name
        ):
            self._next_step_planner = NextStepPlanner(llm, model_name)
            self._next_step_planner_llm = llm
            self._next_step_planner_model = model_name
        return self._next_step_planner

    def _default_tool_agent_key(self) -> str:
        if RAG_TOOL_AGENT_KEY in self._catalog.tool_agent_keys:
            return RAG_TOOL_AGENT_KEY
        return (
            self._catalog.tool_agent_keys[0]
            if self._catalog.tool_agent_keys
            else DEFAULT_TOOL_AGENT_KEY
        )

    def _build_enrich_setup(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        router: ThinkingRouter | None,
    ) -> _EnrichSetup:
        catalog_tools = self._catalog.catalog_tool_names()
        has_tools = bool(catalog_tools)
        system_prompt = self.system_prompt
        if RAG_TOOL_AGENT_KEY in self._catalog.tool_agent_keys:
            system_prompt = DEFAULT_SYSTEM_PROMPT_RAG

        user_query = context.query
        router_decision: RouteDecision | None = None
        router_response_format: dict[str, Any] | None = None
        route_plan = None
        default_key = self._default_tool_agent_key()

        if router is not None and has_tools:
            route_plan = router.plan_enrich_unified(
                context.query,
                history=context.history,
                has_tools=True,
                has_context=False,
                available_tools=catalog_tools,
                default_tool_agent_key=default_key,
            )
            router_decision = route_plan.decision
            router_response_format = router_decision.final_response_format
            for hint in route_plan.tool_hints or []:
                hint.name = self._catalog.resolve_hint_tool_name(
                    hint.name, route_plan.tool_agent_key
                )
            user_query = route_plan.rewritten_query or context.query
            logger.debug(
                "%s=%s %s=%s",
                obs_fields.LLM_RESPONSE_PHASE,
                RoutePhase.ENRICH.value,
                obs_fields.TOOL_AGENT_KEY,
                route_plan.tool_agent_key,
            )

        if has_tools and not (
            route_plan is not None and route_plan.answerable is False
        ):
            system_prompt = system_prompt + ENRICH_PHASE_APPENDIX

        if router is not None and has_tools:
            system_prompt = append_router_tool_hints(
                system_prompt,
                route_plan,
                hints_header="Router enrich hints (soft; use when valid):",
            )

        messages = self.build_messages(
            system_prompt,
            user_query,
            chat_history=context.history,
        )
        opts = ExaoneGenerateOptions(
            tools=self.tools if has_tools else None,
            max_new_tokens=8192,
            enable_thinking=(
                router_decision.enable_thinking if router_decision else bool(has_tools)
            ),
            temperature=(router_decision.temperature if router_decision else 1.0),
            top_p=(router_decision.top_p if router_decision else 0.95),
            response_format=None,
        )
        return _EnrichSetup(
            messages=messages,
            options=opts,
            router_response_format=router_response_format,
            user_query=user_query,
            enrich_route_decision=router_decision,
            route_plan=route_plan,
        )

    def run(
        self,
        context: AgentContext,
        *,
        llm: ExaoneClient | None = None,
        output_pipeline: StructuredOutputPipeline | None = None,
        verbose: bool = False,
    ) -> AgentResult:
        if llm is None:
            return AgentResult(
                success=False,
                content="",
                error="ToolAgent requires ExaoneClient",
            )

        trace = LlmCallTrace()
        trace_token = set_active_llm_trace(trace)
        try:
            return self._attach_llm_calls_metadata(
                self._run_with_tools(
                    context,
                    llm,
                    output_pipeline=output_pipeline,
                    verbose=verbose,
                )
            )
        finally:
            reset_active_llm_trace(trace_token)

    def _run_with_tools(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        output_pipeline: StructuredOutputPipeline | None,
        verbose: bool,
    ) -> AgentResult:
        catalog_tools = self._catalog.catalog_tool_names()
        if not catalog_tools:
            return self._run_finalize_only(
                context,
                llm,
                output_pipeline=output_pipeline,
                verbose=verbose,
            )

        planner = (
            self._get_next_step_planner(llm) if self.use_next_step_planner else None
        )
        router = self._get_thinking_router(llm) if self.use_thinking_router else None
        run_state = EnrichRunState()
        catalog_entries = self._catalog.catalog_entries_for_planner()

        early = self._phase_preflight(
            context,
            llm,
            planner=planner,
            router=router,
            run_state=run_state,
            catalog_entries=catalog_entries,
            output_pipeline=output_pipeline,
            verbose=verbose,
        )
        if early is not None:
            return early

        setup = self._build_enrich_setup(context, llm, router=router)
        early = self._phase_unified_not_answerable(
            context,
            llm,
            planner=planner,
            setup=setup,
            run_state=run_state,
            router=router,
            output_pipeline=output_pipeline,
            verbose=verbose,
        )
        if early is not None:
            return early

        loop_messages, last_content, enrich_turns, stop_error = self._phase_enrich_loop(
            context,
            llm,
            setup=setup,
            planner=planner,
            run_state=run_state,
            catalog_entries=catalog_entries,
            verbose=verbose,
        )
        if stop_error is not None:
            return AgentResult(
                success=False,
                content=last_content,
                error=stop_error,
                metadata=self._enrich_metadata(run_state, enrich_turns),
            )

        return self._finalize_after_enrich(
            context,
            llm,
            messages=loop_messages,
            router=router,
            run_state=run_state,
            output_pipeline=output_pipeline,
            verbose=verbose,
            router_response_format=setup.router_response_format,
            enrich_route_decision=setup.enrich_route_decision,
            last_content=last_content,
            enrich_turns=enrich_turns,
        )

    def _phase_preflight(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        planner: NextStepPlanner | None,
        router: ThinkingRouter | None,
        run_state: EnrichRunState,
        catalog_entries: list[dict[str, Any]],
        output_pipeline: StructuredOutputPipeline | None,
        verbose: bool,
    ) -> AgentResult | None:
        if not self._should_run_catalog_screen_llm(planner, router):
            return None
        # (en) type: ignore[union-attr] — planner is optional; screen_catalog exists when screening runs.
        # (kr) type: ignore[union-attr] — planner 는 optional; screening 시 screen_catalog 가 있다.
        # type: ignore[union-attr]
        screen = planner.screen_catalog(
            context.query,
            catalog=catalog_entries,
            history=context.history,
        )
        if screen.answerable:
            return None
        run_state.stop_reason = EnrichStopReason.NOT_ANSWERABLE
        return self._finalize_after_enrich(
            context,
            llm,
            messages=self.build_messages(
                self.system_prompt,
                context.query,
                chat_history=context.history,
            ),
            router=router,
            run_state=run_state,
            output_pipeline=output_pipeline,
            verbose=verbose,
            router_response_format=None,
        )

    def _phase_unified_not_answerable(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        planner: NextStepPlanner | None,
        setup: _EnrichSetup,
        run_state: EnrichRunState,
        router: ThinkingRouter | None,
        output_pipeline: StructuredOutputPipeline | None,
        verbose: bool,
    ) -> AgentResult | None:
        if setup.route_plan is None:
            return None
        if setup.route_plan.answerable is not False:
            return None
        run_state.stop_reason = EnrichStopReason.NOT_ANSWERABLE
        return self._finalize_after_enrich(
            context,
            llm,
            messages=setup.messages,
            router=router,
            run_state=run_state,
            output_pipeline=output_pipeline,
            verbose=verbose,
            router_response_format=setup.router_response_format,
            enrich_route_decision=setup.enrich_route_decision,
        )

    def _phase_enrich_loop(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        setup: _EnrichSetup,
        planner: NextStepPlanner | None,
        run_state: EnrichRunState,
        catalog_entries: list[dict[str, Any]],
        verbose: bool,
    ) -> tuple[list[Any], str, int, str | None]:
        ledger_executor = wrap_tool_executor_with_ledger(
            self.tool_executor,
            run_state.ledger,
            max_tool_invocations=self.max_tool_invocations,
        )
        enrich_turns = 0
        loop_messages = setup.messages
        last_content = ""

        while enrich_turns < self.max_enrich_turns:
            loop_result = self._run_reason_tool_loop(
                llm,
                loop_messages,
                tools=self.tools,
                tool_executor=ledger_executor,
                options=setup.options,
                max_turns=1,
                verbose=verbose,
                llm_call_phase=AgentRunPhase.ENRICH_REACT.value,
            )
            loop_messages = loop_result.messages
            last_content = loop_result.final_content
            enrich_turns += 1

            if loop_result.error:
                run_state.stop_reason = EnrichStopReason.ERROR
                return loop_messages, last_content, enrich_turns, loop_result.error

            if not _last_assistant_had_tool_calls(loop_messages):
                run_state.stop_reason = EnrichStopReason.NO_TOOL_CALLS
                break

            if run_state.ledger.invocation_count >= self.max_tool_invocations:
                run_state.stop_reason = EnrichStopReason.BUDGET_EXHAUSTED
                break

            if planner is None:
                continue

            progress = planner.evaluate_progress(
                context.query,
                messages=loop_messages,
                catalog=catalog_entries,
                ledger=run_state.ledger,
                budget_remaining={
                    "enrich_turns_remaining": self.max_enrich_turns - enrich_turns,
                    "tool_invocations_remaining": (
                        self.max_tool_invocations - run_state.ledger.invocation_count
                    ),
                },
            )
            run_state.last_progress = progress
            logger.debug(
                "%s=%s %s=%s %s=%s",
                obs_fields.PROGRESS_ACTION,
                progress.action,
                obs_fields.CONTEXT_SUFFICIENT,
                progress.sufficient,
                "no_progress",
                progress.no_progress,
            )

            if progress.should_finalize:
                if progress.sufficient:
                    run_state.stop_reason = EnrichStopReason.SUFFICIENT
                elif progress.no_progress:
                    run_state.stop_reason = EnrichStopReason.NO_PROGRESS
                else:
                    run_state.stop_reason = EnrichStopReason.SUFFICIENT
                break

            if progress.next_tool_calls:
                loop_messages = append_progress_tool_hint(
                    loop_messages, progress.next_tool_calls[0]
                )

        if run_state.stop_reason is None and enrich_turns >= self.max_enrich_turns:
            run_state.stop_reason = EnrichStopReason.BUDGET_EXHAUSTED

        return loop_messages, last_content, enrich_turns, None

    def _finalize_after_enrich(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        messages: list[Any],
        router: ThinkingRouter | None,
        run_state: EnrichRunState,
        output_pipeline: StructuredOutputPipeline | None,
        verbose: bool,
        router_response_format: dict[str, Any] | None,
        enrich_route_decision: RouteDecision | None = None,
        last_content: str = "",
        enrich_turns: int = 0,
    ) -> AgentResult:
        has_context = run_state.ledger.invocation_count > 0
        finalize_plan = (
            router.plan_finalize(
                context.query,
                history=context.history,
                has_context=has_context,
                enrich_decision=enrich_route_decision,
                default_answer_tool_agent=(
                    RAG_TOOL_AGENT_KEY
                    if RAG_TOOL_AGENT_KEY in self._catalog.tool_agent_keys
                    else ANSWER_TOOL_AGENT_KEY
                ),
            )
            if router
            else None
        )

        answer_key = (
            finalize_plan.answer_tool_agent_key if finalize_plan else ANSWER_TOOL_AGENT_KEY
        )
        finalize_messages = _replace_system_prompt(
            messages,
            _finalize_system_prompt(answer_key, self.system_prompt),
        )
        final_response_format = (
            finalize_plan.decision.final_response_format
            if finalize_plan
            else router_response_format
        )
        final_content, _reasoning = self.request_final_turn(
            llm,
            finalize_messages,
            max_new_tokens=4096,
            response_format=final_response_format,
            verbose=verbose,
        )
        if not final_content:
            final_content = last_content

        structured = self._ensure_json_output(final_content, output_pipeline)
        meta = self._enrich_metadata(run_state, enrich_turns)
        meta[obs_fields.LLM_RESPONSE_PHASE] = RoutePhase.FINALIZE.value
        meta[obs_fields.ANSWER_TOOL_AGENT_KEY] = answer_key
        return AgentResult(
            success=structured.success,
            content=final_content,
            structured=structured.data,
            error=structured.error,
            metadata=meta,
        )

    @staticmethod
    def _enrich_metadata(run_state: EnrichRunState, enrich_turns: int) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "turns_used": enrich_turns,
            obs_fields.LLM_RESPONSE_PHASE: RoutePhase.ENRICH.value,
            obs_fields.TOOL_INVOCATIONS: run_state.ledger.invocation_count,
            obs_fields.DUPLICATES_BLOCKED: run_state.ledger.duplicates_blocked,
        }
        if run_state.stop_reason is not None:
            meta[obs_fields.ENRICH_STOP_REASON] = run_state.stop_reason.value
        if run_state.last_progress is not None:
            meta[obs_fields.PROGRESS_ACTION] = run_state.last_progress.action
            meta[obs_fields.CONTEXT_SUFFICIENT] = run_state.last_progress.sufficient
        return meta

    def _run_finalize_only(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        output_pipeline: StructuredOutputPipeline | None = None,
        verbose: bool = False,
    ) -> AgentResult:
        messages = self.build_messages(self.system_prompt, context.query, chat_history=context.history)
        router = self._get_thinking_router(llm) if self.use_thinking_router else None
        response_format = None
        if router:
            decision = router.route(context.query, history=context.history, has_tools=False)
            response_format = decision.final_response_format
        final_content, _ = self.request_final_turn(
            llm,
            messages,
            response_format=response_format,
            verbose=verbose,
        )
        structured = self._ensure_json_output(final_content, output_pipeline)
        return AgentResult(
            success=structured.success,
            content=final_content,
            structured=structured.data,
            error=structured.error,
        )

    def run_stream(
        self,
        context: AgentContext,
        *,
        llm: ExaoneClient | None = None,
        verbose: bool = False,
        stream_llm: bool = False,
        stream_enrich_reasoning: bool = False,
    ) -> Iterator[AgentEvent]:
        if llm is None:
            yield AgentEvent(type="error", payload={"message": "ToolAgent requires ExaoneClient"})
            yield AgentEvent(
                type="run_end",
                payload={
                    "final_content": "",
                    "turns_used": 0,
                    "error": "ToolAgent requires ExaoneClient",
                },
            )
            return

        yield from self._iter_agent_pipeline(
            context,
            llm,
            verbose=verbose,
            stream_llm=stream_llm,
            stream_enrich_reasoning=stream_enrich_reasoning,
            attach_llm_trace=True,
        )

    def _iter_agent_pipeline(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        verbose: bool,
        stream_llm: bool,
        stream_enrich_reasoning: bool,
        attach_llm_trace: bool = False,
    ) -> Iterator[AgentEvent]:
        trace_token = None
        if attach_llm_trace:
            trace_token = set_active_llm_trace(LlmCallTrace())
        try:
            yield from self._iter_agent_pipeline_body(
                context,
                llm,
                verbose=verbose,
                stream_llm=stream_llm,
                stream_enrich_reasoning=stream_enrich_reasoning,
            )
        finally:
            if trace_token is not None:
                try:
                    reset_active_llm_trace(trace_token)
                except ValueError:
                    # (en) FastAPI/Starlette may close the generator in another thread context.
                    # (kr) FastAPI/Starlette 가 다른 스레드 컨텍스트에서 generator 를 닫을 수 있다.
                    logger.debug("llm trace reset skipped (stream context mismatch)")

    def _iter_agent_pipeline_body(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        verbose: bool,
        stream_llm: bool,
        stream_enrich_reasoning: bool,
    ) -> Iterator[AgentEvent]:
        catalog_tools = self._catalog.catalog_tool_names()
        yield AgentEvent(
            type="run_start",
            turn=0,
            payload={
                "stream_llm": stream_llm,
                "stream_enrich_reasoning": stream_enrich_reasoning,
                "has_tools": bool(catalog_tools),
            },
        )

        if not catalog_tools:
            yield from self._iter_finalize_only_stream(
                context,
                llm,
                verbose=verbose,
                stream_llm=stream_llm,
            )
            return

        planner = (
            self._get_next_step_planner(llm) if self.use_next_step_planner else None
        )
        router = self._get_thinking_router(llm) if self.use_thinking_router else None
        run_state = EnrichRunState()
        catalog_entries = self._catalog.catalog_entries_for_planner()

        yield self._phase_event("phase_start", PHASE_PREFLIGHT)
        early_messages: list[Any] | None = None
        if self._should_run_catalog_screen_llm(planner, router):
            # (en) type: ignore[union-attr] — planner is optional; screen_catalog exists when screening runs.
            # (kr) type: ignore[union-attr] — planner 는 optional; screening 시 screen_catalog 가 있다.
            # type: ignore[union-attr]
            screen = planner.screen_catalog(
                context.query,
                catalog=catalog_entries,
                history=context.history,
            )
            yield AgentEvent(
                type="planner_end",
                turn=0,
                payload={
                    "kind": "catalog_screen",
                    "answerable": screen.answerable,
                    "tool_agent_key": screen.tool_agent_key,
                },
            )
            if not screen.answerable:
                run_state.stop_reason = EnrichStopReason.NOT_ANSWERABLE
                early_messages = self.build_messages(
                    self.system_prompt,
                    context.query,
                    chat_history=context.history,
                )
        yield self._phase_event(
            "phase_end",
            PHASE_PREFLIGHT,
            stop_reason=(
                run_state.stop_reason.value if run_state.stop_reason else None
            ),
        )

        if early_messages is not None:
            yield from self._iter_finalize_phase(
                context,
                llm,
                messages=early_messages,
                router=router,
                run_state=run_state,
                verbose=verbose,
                stream_llm=stream_llm,
                router_response_format=None,
                enrich_route_decision=None,
                enrich_turns=0,
            )
            return

        setup = self._build_enrich_setup(context, llm, router=router)
        if (
            setup.route_plan is not None
            and setup.route_plan.answerable is False
        ):
            run_state.stop_reason = EnrichStopReason.NOT_ANSWERABLE
            yield from self._iter_finalize_phase(
                context,
                llm,
                messages=setup.messages,
                router=router,
                run_state=run_state,
                verbose=verbose,
                stream_llm=stream_llm,
                router_response_format=setup.router_response_format,
                enrich_route_decision=setup.enrich_route_decision,
                enrich_turns=0,
            )
            return

        yield self._phase_event("phase_start", PHASE_ENRICH, max_turns=self.max_enrich_turns)
        ledger_executor = wrap_tool_executor_with_ledger(
            self.tool_executor,
            run_state.ledger,
            max_tool_invocations=self.max_tool_invocations,
        )
        enrich_turns = 0
        loop_messages = setup.messages
        last_content = ""
        enrich_error: str | None = None

        while enrich_turns < self.max_enrich_turns:
            enrich_turns += 1
            for ev in self._iter_reason_tool_loop(
                llm,
                loop_messages,
                tools=self.tools,
                tool_executor=ledger_executor,
                options=setup.options,
                max_turns=1,
                verbose=verbose,
                stream_llm=stream_enrich_reasoning,
                llm_call_phase=AgentRunPhase.ENRICH_REACT.value,
            ):
                if ev.type == "run_start":
                    continue
                if ev.type == "run_end":
                    loop_messages = ev.payload.get("messages", loop_messages)
                    last_content = ev.payload.get("final_content", "")
                    enrich_error = ev.payload.get("error")
                    continue
                if ev.type in ("turn_start", "llm_delta", "llm_end", "tool_start", "tool_end", "error"):
                    yield AgentEvent(
                        type=ev.type,
                        turn=enrich_turns,
                        payload={**ev.payload, "phase": PHASE_ENRICH},
                    )
                else:
                    yield ev

            if enrich_error:
                run_state.stop_reason = EnrichStopReason.ERROR
                break

            if not _last_assistant_had_tool_calls(loop_messages):
                run_state.stop_reason = EnrichStopReason.NO_TOOL_CALLS
                break

            if run_state.ledger.invocation_count >= self.max_tool_invocations:
                run_state.stop_reason = EnrichStopReason.BUDGET_EXHAUSTED
                break

            if planner is None:
                continue

            progress = planner.evaluate_progress(
                context.query,
                messages=loop_messages,
                catalog=catalog_entries,
                ledger=run_state.ledger,
                budget_remaining={
                    "enrich_turns_remaining": self.max_enrich_turns - enrich_turns,
                    "tool_invocations_remaining": (
                        self.max_tool_invocations - run_state.ledger.invocation_count
                    ),
                },
            )
            run_state.last_progress = progress
            yield AgentEvent(
                type="planner_end",
                turn=enrich_turns,
                payload={
                    "kind": "evaluate_progress",
                    "action": progress.action,
                    "sufficient": progress.sufficient,
                    "no_progress": progress.no_progress,
                    "should_finalize": progress.should_finalize,
                },
            )

            if progress.should_finalize:
                if progress.sufficient:
                    run_state.stop_reason = EnrichStopReason.SUFFICIENT
                elif progress.no_progress:
                    run_state.stop_reason = EnrichStopReason.NO_PROGRESS
                else:
                    run_state.stop_reason = EnrichStopReason.SUFFICIENT
                break

            if progress.next_tool_calls:
                loop_messages = append_progress_tool_hint(
                    loop_messages, progress.next_tool_calls[0]
                )

        if run_state.stop_reason is None and enrich_turns >= self.max_enrich_turns:
            run_state.stop_reason = EnrichStopReason.BUDGET_EXHAUSTED

        yield self._phase_event(
            "phase_end",
            PHASE_ENRICH,
            enrich_turns=enrich_turns,
            stop_reason=(
                run_state.stop_reason.value if run_state.stop_reason else None
            ),
        )

        if enrich_error:
            meta = self._enrich_metadata(run_state, enrich_turns)
            yield AgentEvent(type="error", payload={"message": enrich_error, **meta})
            yield AgentEvent(
                type="run_end",
                turn=enrich_turns,
                payload={
                    "final_content": last_content,
                    "turns_used": enrich_turns,
                    "error": enrich_error,
                    "phase": PHASE_ENRICH,
                    **meta,
                    **self._llm_calls_payload(),
                },
            )
            return

        yield from self._iter_finalize_phase(
            context,
            llm,
            messages=loop_messages,
            router=router,
            run_state=run_state,
            verbose=verbose,
            stream_llm=stream_llm,
            router_response_format=setup.router_response_format,
            enrich_route_decision=setup.enrich_route_decision,
            last_content=last_content,
            enrich_turns=enrich_turns,
        )

    def _llm_calls_payload(self) -> dict[str, Any]:
        trace = get_active_llm_trace()
        if trace is None or not trace.records:
            return {}
        return {obs_fields.LLM_CALLS: trace.to_metadata_list()}

    def _iter_finalize_only_stream(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        verbose: bool,
        stream_llm: bool,
    ) -> Iterator[AgentEvent]:
        yield self._phase_event("phase_start", PHASE_FINALIZE, finalize_only=True)
        messages = self.build_messages(
            self.system_prompt, context.query, chat_history=context.history
        )
        router = self._get_thinking_router(llm) if self.use_thinking_router else None
        response_format = None
        if router:
            decision = router.route(
                context.query, history=context.history, has_tools=False
            )
            response_format = decision.final_response_format
        yield from self._iter_finalize_llm_turn(
            llm,
            messages,
            response_format=response_format,
            stream_llm=stream_llm,
            enrich_turns=0,
            run_state=EnrichRunState(),
            phase_end_payload={"finalize_only": True},
        )

    def _iter_finalize_phase(
        self,
        context: AgentContext,
        llm: ExaoneClient,
        *,
        messages: list[Any],
        router: ThinkingRouter | None,
        run_state: EnrichRunState,
        verbose: bool,
        stream_llm: bool,
        router_response_format: dict[str, Any] | None,
        enrich_route_decision: RouteDecision | None,
        last_content: str = "",
        enrich_turns: int = 0,
    ) -> Iterator[AgentEvent]:
        yield self._phase_event("phase_start", PHASE_FINALIZE)
        has_context = run_state.ledger.invocation_count > 0
        finalize_plan = (
            router.plan_finalize(
                context.query,
                history=context.history,
                has_context=has_context,
                enrich_decision=enrich_route_decision,
                default_answer_tool_agent=(
                    RAG_TOOL_AGENT_KEY
                    if RAG_TOOL_AGENT_KEY in self._catalog.tool_agent_keys
                    else ANSWER_TOOL_AGENT_KEY
                ),
            )
            if router
            else None
        )
        answer_key = (
            finalize_plan.answer_tool_agent_key if finalize_plan else ANSWER_TOOL_AGENT_KEY
        )
        finalize_messages = _replace_system_prompt(
            messages,
            _finalize_system_prompt(answer_key, self.system_prompt),
        )
        final_response_format = (
            finalize_plan.decision.final_response_format
            if finalize_plan
            else router_response_format
        )
        yield from self._iter_finalize_llm_turn(
            llm,
            finalize_messages,
            response_format=final_response_format,
            stream_llm=stream_llm,
            enrich_turns=enrich_turns,
            run_state=run_state,
            answer_key=answer_key,
            last_content=last_content,
            phase_end_payload={"answer_tool_agent_key": answer_key},
        )

    def _iter_finalize_llm_turn(
        self,
        llm: ExaoneClient,
        messages: list[Any],
        *,
        response_format: dict[str, Any] | None,
        stream_llm: bool,
        enrich_turns: int,
        run_state: EnrichRunState,
        answer_key: str = ANSWER_TOOL_AGENT_KEY,
        last_content: str = "",
        phase_end_payload: dict[str, Any] | None = None,
    ) -> Iterator[AgentEvent]:
        from exaone.llm import ExaoneGenerateOptions, ExaoneMessage
        from exaone.llm.response_quality import FINAL_TURN_JSON_NUDGE

        final_messages = list(messages) + [
            ExaoneMessage(role="user", content=FINAL_TURN_JSON_NUDGE),
        ]
        final_opts = ExaoneGenerateOptions(
            max_new_tokens=4096,
            enable_thinking=False,
            tools=None,
            response_format=response_format,
        )
        content = last_content
        for ev in self._iter_single_llm_turn(
            llm,
            final_messages,
            options=final_opts,
            stream_llm=stream_llm,
        ):
            if ev.type == "run_start":
                continue
            if ev.type == "run_end":
                content = ev.payload.get("final_content", "") or last_content
                error = ev.payload.get("error")
                meta = self._enrich_metadata(run_state, enrich_turns)
                meta[obs_fields.LLM_RESPONSE_PHASE] = RoutePhase.FINALIZE.value
                meta[obs_fields.ANSWER_TOOL_AGENT_KEY] = answer_key
                meta.update(self._llm_calls_payload())
                yield self._phase_event(
                    "phase_end",
                    PHASE_FINALIZE,
                    **(phase_end_payload or {}),
                )
                yield AgentEvent(
                    type="run_end",
                    turn=enrich_turns,
                    payload={
                        "final_content": content,
                        "turns_used": enrich_turns,
                        "error": error,
                        "phase": PHASE_FINALIZE,
                        **meta,
                    },
                )
                continue
            yield AgentEvent(
                type=ev.type,
                turn=ev.turn,
                payload={**ev.payload, "phase": PHASE_FINALIZE},
            )


def _last_assistant_had_tool_calls(messages: list[Any]) -> bool:
    for msg in reversed(messages):
        if getattr(msg, "role", None) == "assistant":
            return bool(getattr(msg, "tool_calls", None))
    return False


def _replace_system_prompt(messages: list[Any], new_system: str) -> list[Any]:
    out: list[Any] = []
    replaced = False
    for msg in messages:
        if getattr(msg, "role", None) == "system" and not replaced:
            out.append(ExaoneMessage(role="system", content=new_system))
            replaced = True
        else:
            out.append(msg)
    if not replaced:
        out.insert(0, ExaoneMessage(role="system", content=new_system))
    return out
