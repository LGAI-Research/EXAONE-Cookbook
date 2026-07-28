"""
(en) Common agent interface.
K-EXAONE is a single agent: reasoning (thinking) → tool calling → (repeat) only.
Default implementation is a pure Python for-loop reason → tool loop.

Pattern reference: LangChain Agent (ChatPromptTemplate + MessagesPlaceholder + agent_scratchpad)
  - https://friendli.ai/docs/guides/tutorials/build-an-agent-with-langchain
  - system / chat_history / user input / (tool results handled as assistant→tool messages inside the loop)

(kr) Agent 공통 인터페이스입니다.
K-EXAONE는 싱글 에이전트로, reasoning(thinking) → tool calling → (반복) 구조만 지원합니다.
순수 Python for-loop 기반 reason → tool 루프가 기본 구현입니다.

패턴 참고: LangChain Agent (ChatPromptTemplate + MessagesPlaceholder + agent_scratchpad)
  - https://friendli.ai/docs/guides/tutorials/build-an-agent-with-langchain
  - system / chat_history / user input / (tool 결과는 루프 내 assistant→tool 메시지로 처리합니다)
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterator, Literal, Union

logger = logging.getLogger(__name__)

# (en) Avoid circular imports via TYPE_CHECKING
# (kr) 순환 참조 방지를 위해 TYPE_CHECKING을 사용한다
from typing import TYPE_CHECKING

from exaone.context_management.messages import (
    cap_max_new_tokens,
    compress_messages_for_turn,
    ensure_input_within_limit,
    estimate_tokens_from_messages,
    message_role,
    split_leading_system,
)
from exaone.output.unicode_normalizer import normalize_json_string_values, normalize_unicode_string
from exaone.tools.results import (
    format_tool_result_for_llm,
    tool_executor_return_indicates_error,
    tool_failure_payload,
)

if TYPE_CHECKING:
    from exaone.agents.events import AgentEvent
    from exaone.llm import ExaoneClient, ExaoneMessage
    from exaone.output import StructuredOutputPipeline, StructuredResponse


@dataclass
class ChatHistory:
    """(en) One chat-history turn; typed form usable alongside dict-based input.

    (kr) 대화 히스토리 한 턴입니다. dict 기반 입력과 함께 사용 가능한 typed 형태입니다.
    """
    role: Literal["user", "assistant"]
    content: str


ChatHistoryTurn = Union[ChatHistory, dict[str, Any]]


@dataclass
class AgentContext:
    """
    (en) Shared execution context for an agent run (memory/args only, no DB).
    history: LangChain-style chat_history.
      - typed: [ChatHistory(...), ...]
      - legacy: [{"role": "user"|"assistant", "content": str}, ...] (backward compatible)

    (kr) Agent 실행 시 공유 컨텍스트입니다(DB 없이 메모리/인자만 사용).
    history: LangChain 스타일 chat_history입니다.
      - typed: [ChatHistory(...), ...]
      - legacy: [{"role": "user"|"assistant", "content": str}, ...] (하위 호환)
    """
    query: str
    history: list[ChatHistory | dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """(en) Agent run result; serialized to JSON by the output layer.

    (kr) Agent 실행 결과입니다. output 계층에서 JSON으로 직렬화됩니다.
    """
    success: bool
    # (en) Raw text before post-processing
    # (kr) 후처리 전 원문
    content: str
    # (en) StructuredResponse.data when present, else None
    # (kr) StructuredResponse.data가 있으면 해당 값, 없으면 None
    structured: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    # (en) Chain-of-thought when enable_thinking (rag_agent compatibility)
    # (kr) enable_thinking 시 chain-of-thought(rag_agent 호환용)
    reasoning_content: str | None = None


# (en) Single-agent reason-tool loop result (internal)
# (kr) 싱글 에이전트 reason-tool 루프 결과(내부용)
@dataclass
class _ReasonToolLoopResult:
    final_content: str
    messages: list[Any]
    turns_used: int
    error: str | None = None
    total_latency_ms: float = 0.0
    # (en) True iff the loop exited after running tool calls on the final turn
    # rather than producing a tool-call-free assistant message. Callers driving
    # the loop with a small max_turns (e.g. ToolAgent.enrich step uses 1) treat
    # this as an intended hand-off rather than an error.
    # (kr) 마지막 턴이 자연어 응답이 아니라 tool 호출 실행으로 끝났을 때 True.
    # 작은 max_turns(예: ToolAgent.enrich step은 1)로 루프를 운전하는 호출자가
    # 이를 의도된 hand-off로 인식해 ERROR로 오인하지 않도록 한다.
    terminated_after_tool_round: bool = False


class BaseAgent(ABC):
    """(en) Single-agent base: reasoning → tool calling → (repeat).

    (kr) 싱글 에이전트 기반입니다: reasoning → tool calling → (반복).
    """

    @staticmethod
    def normalize_chat_history_turns(
        chat_history: list[ChatHistoryTurn] | None,
    ) -> list[dict[str, str]]:
        """(en) Normalize AgentContext-style history to dict turns.

        (kr) AgentContext 스타일 history를 dict turn 목록으로 정규화합니다.
        """
        out: list[dict[str, str]] = []
        for turn in chat_history or []:
            if isinstance(turn, ChatHistory):
                out.append({"role": turn.role, "content": turn.content})
            elif isinstance(turn, dict):
                out.append({
                    "role": str(turn.get("role") or "user"),
                    "content": str(turn.get("content") or ""),
                })
        return out

    @abstractmethod
    def run(
        self,
        context: AgentContext,
        *,
        llm: ExaoneClient | None = None,
        output_pipeline: StructuredOutputPipeline | None = None,
        verbose: bool = False,
    ) -> AgentResult:
        """(en) Run inference from context; log reason/tool turns when verbose=True.

        (kr) 컨텍스트를 받아 추론 결과를 반환합니다. verbose=True이면 reason/tool 턴을 로깅합니다.
        """
        ...

    @staticmethod
    def build_messages(
        system_prompt: str,
        user_content: str,
        chat_history: list[ChatHistory | dict[str, Any]] | None = None,
    ) -> list[Any]:
        """
        (en) Build LangChain-style prompt order: [system, ...chat_history, user].
        Same order as ChatPromptTemplate.from_messages([system, MessagesPlaceholder("chat_history"), user]).
        chat_history:
          - [ChatHistory(role="user"|"assistant", content="..."), ...]
          - [{"role": "user"|"assistant", "content": str}, ...] (legacy)

        (kr) LangChain 스타일 프롬프트를 구성합니다: [system, ...chat_history, user].
        ChatPromptTemplate.from_messages([system, MessagesPlaceholder("chat_history"), user])와 동일한 순서입니다.
        chat_history:
          - [ChatHistory(role="user"|"assistant", content="..."), ...]
          - [{"role": "user"|"assistant", "content": str}, ...] (legacy)
        """
        from exaone.llm import ExaoneMessage

        # (en) Replace UTC date placeholder so the agent knows "today" at run time
        # (kr) 실행 시점 UTC 날짜 플레이스홀더를 치환해 에이전트가 "오늘"을 알 수 있게 한다
        if "{{CURRENT_DATE_UTC}}" in system_prompt:
            utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            system_prompt = system_prompt.replace("{{CURRENT_DATE_UTC}}", utc_now)

        messages: list[Any] = [
            ExaoneMessage(role="system", content=system_prompt),
        ]
        for turn in BaseAgent.normalize_chat_history_turns(chat_history):
            role = turn.get("role") or "user"
            content = turn.get("content") or ""
            if role in ("user", "assistant") and content:
                messages.append(ExaoneMessage(role=role, content=content))
        messages.append(ExaoneMessage(role="user", content=user_content))
        return messages

    @staticmethod
    def should_request_final_turn(
        content: str,
        structured: Any,
        *,
        output_pipeline: StructuredOutputPipeline | None = None,
    ) -> bool:
        """(en) True when an agent-level final turn (thinking off + optional schema) may help.

        (kr) 에이전트 수준 final turn(thinking off + 선택적 schema)이 도움이 될 때 True입니다.
        """
        if not (content or "").strip():
            return True
        if output_pipeline is None or structured is None:
            return False
        if getattr(structured, "success", True):
            return False
        err = str(getattr(structured, "error", "") or "").lower()
        return "no json start" in err

    @staticmethod
    def request_final_turn(
        llm: "ExaoneClient",
        messages: list[Any],
        *,
        max_new_tokens: int = 1024,
        response_format: dict[str, Any] | None = None,
        nudge: str | None = None,
        verbose: bool = False,
    ) -> tuple[str, str | None]:
        """
        (en) Final completion with thinking disabled. Returns (content, reasoning_content).

        (kr) thinking을 끈 상태로 최종 completion을 수행합니다. (content, reasoning_content)를 반환합니다.
        """
        from exaone.llm import ExaoneGenerateOptions, ExaoneMessage
        from exaone.llm.response_quality import FINAL_TURN_JSON_NUDGE

        final_turn_messages = list(messages) + [
            ExaoneMessage(role="user", content=nudge or FINAL_TURN_JSON_NUDGE),
        ]
        final_opts = ExaoneGenerateOptions(
            max_new_tokens=max_new_tokens,
            enable_thinking=False,
            tools=None,
            response_format=response_format,
        )
        try:
            from exaone.agents.run_trace import AgentRunPhase, get_active_llm_trace, traced_chat

            if get_active_llm_trace() is not None:
                resp = traced_chat(
                    llm,
                    final_turn_messages,
                    final_opts,
                    phase=AgentRunPhase.FINAL_ANSWER,
                )
            else:
                resp = llm.chat(final_turn_messages, options=final_opts)
            return resp.content or "", getattr(resp, "reasoning_content", None)
        except Exception as e:
            if verbose:
                logger.info("Final-turn retry failed: %s", str(e))
            return "", None

    def _ensure_json_output(
        self,
        raw_content: str,
        pipeline: StructuredOutputPipeline | None,
    ) -> StructuredResponse:
        """(en) Normalize response to JSON via the output layer.
        When pipeline=None, skip parse/validation and return raw content as-is.

        (kr) output 계층을 통해 JSON 형식 응답으로 정규화합니다.
        pipeline=None이면 파싱/검증을 스킵하고 raw content를 그대로 반환합니다.
        """
        if pipeline is None:
            from exaone.output import StructuredResponse
            return StructuredResponse(
                success=True,
                data={"answer": raw_content},
                raw_content=raw_content,
            )
        return pipeline.process(raw_content)

    @staticmethod
    def _iter_reason_tool_loop(
        llm: "ExaoneClient",
        messages: list["ExaoneMessage"],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_executor: Callable[[str, dict[str, Any]], Any],
        options: Any | None = None,
        max_turns: int = 10,
        max_consecutive_tool_errors: int = 3,
        verbose: bool = False,
        stream_llm: bool = False,
        llm_call_phase: str | None = None,
    ) -> Iterator["AgentEvent"]:
        """(en) Yield semantic AgentEvent during reason → tool loop. Final event is run_end with loop metadata.

        (kr) reason → tool 루프 동안 semantic AgentEvent를 yield합니다. 마지막 이벤트는 루프 메타데이터가 담긴 run_end입니다.
        """
        from exaone.agents.events import AgentEvent
        from exaone.agents.run_trace import get_active_llm_trace, traced_chat
        from exaone.llm import ExaoneMessage, ExaoneGenerateOptions
        from exaone.llm.streaming import stream_chunks_to_response

        if verbose:
            logger.setLevel(logging.INFO)
            if not logging.root.handlers:
                logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")

        opts = options or ExaoneGenerateOptions()
        if tools is not None:
            opts = ExaoneGenerateOptions(
                max_new_tokens=opts.max_new_tokens,
                temperature=opts.temperature,
                top_p=opts.top_p,
                do_sample=opts.do_sample,
                enable_thinking=opts.enable_thinking,
                tools=tools,
                response_format=getattr(opts, "response_format", None),
            )

        state: dict[str, Any] = {
            "messages": list(messages),
            "turn": 0,
            "last_content": "",
            "last_tool_calls": None,
            "error": None,
            "total_latency_ms": 0.0,
            "consecutive_tool_errors": 0,
            "terminated_after_tool_round": False,
        }

        yield AgentEvent(type="run_start", turn=0, payload={"max_turns": max_turns, "stream_llm": stream_llm})

        for _ in range(max_turns):
            msgs = list(state["messages"])
            turn = state.get("turn", 0)
            turn_no = turn + 1
            if verbose and turn > 0:
                logger.info("Finished tool turn, re-entering reason (turn %d)...", turn_no)
            elif verbose:
                logger.info("Entering AgentExecutor chain (reason → tool loop)...")

            yield AgentEvent(type="turn_start", turn=turn_no, payload={})

            msgs, input_error = ensure_input_within_limit(
                msgs, llm, reserved_new_tokens=opts.max_new_tokens
            )
            if input_error is not None:
                state["error"] = input_error
                yield AgentEvent(type="error", turn=turn_no, payload={"message": input_error})
                break
            if len(msgs) == 1 and message_role(msgs[0]) == "user":
                msgs = list(msgs) + [ExaoneMessage(role="user", content="(응답을 이어서 작성해 주세요.)")]
            elif not msgs or not split_leading_system(msgs)[0]:
                msgs = [ExaoneMessage(role="system", content="You are a helpful assistant.")] + list(msgs)

            input_tokens = estimate_tokens_from_messages(msgs)
            capped_max_new = cap_max_new_tokens(input_tokens, opts.max_new_tokens)
            turn_opts = ExaoneGenerateOptions(
                max_new_tokens=capped_max_new,
                temperature=opts.temperature,
                top_p=opts.top_p,
                do_sample=opts.do_sample,
                enable_thinking=opts.enable_thinking,
                tools=opts.tools if hasattr(opts, "tools") else None,
                response_format=getattr(opts, "response_format", None),
            )

            try:
                if stream_llm:
                    collected: list[Any] = []
                    for chunk in llm.chat_stream(msgs, options=turn_opts):
                        collected.append(chunk)
                        if chunk.kind == "text" and chunk.text:
                            yield AgentEvent(
                                type="llm_delta",
                                turn=turn_no,
                                payload={"channel": "content", "text": chunk.text},
                            )
                        elif chunk.kind == "reasoning" and chunk.text:
                            yield AgentEvent(
                                type="llm_delta",
                                turn=turn_no,
                                payload={"channel": "reasoning", "text": chunk.text},
                            )
                        elif chunk.kind == "error":
                            raise RuntimeError(chunk.text or "LLM stream error")
                    resp = stream_chunks_to_response(iter(collected))
                else:
                    if get_active_llm_trace() is not None and llm_call_phase:
                        resp = traced_chat(
                            llm,
                            msgs,
                            turn_opts,
                            phase=llm_call_phase,
                            turn=turn_no,
                        )
                    else:
                        resp = llm.chat(msgs, options=turn_opts)
            except Exception as e:
                state["error"] = str(e)
                yield AgentEvent(type="error", turn=turn_no, payload={"message": str(e)})
                break

            yield AgentEvent(
                type="llm_end",
                turn=turn_no,
                payload={
                    "content_length": len(resp.content or ""),
                    "reasoning_length": len(resp.reasoning_content or ""),
                    "has_tool_calls": bool(resp.tool_calls),
                    "latency_ms": resp.latency_ms,
                },
            )

            assistant_msg = ExaoneMessage(
                role="assistant",
                content=resp.content or "",
                tool_calls=resp.tool_calls,
            )
            new_messages = compress_messages_for_turn(
                msgs + [assistant_msg],
                llm,
                reserved_new_tokens=turn_opts.max_new_tokens,
            )
            state["messages"] = new_messages
            state["last_content"] = resp.content or ""
            state["last_reasoning_content"] = getattr(resp, "reasoning_content", None)
            state["last_tool_calls"] = resp.tool_calls or []
            state["turn"] = turn_no
            state["total_latency_ms"] = state.get("total_latency_ms", 0.0) + (resp.latency_ms or 0.0)

            if not state["last_tool_calls"]:
                break

            tool_msgs = list(state["messages"])
            tool_errors_this_turn = 0
            for tc in state["last_tool_calls"]:
                tid = tc.get("id") or ""
                fn = tc.get("function") or {}
                name = fn.get("name") or "unknown"
                args_str = fn.get("arguments") or "{}"
                args_str = normalize_unicode_string(args_str)
                args_preview = args_str[:200] + ("..." if len(args_str) > 200 else "")

                yield AgentEvent(
                    type="tool_start",
                    turn=turn_no,
                    payload={"tool": name, "args_preview": args_preview},
                )

                try:
                    parsed_args = json.loads(args_str)
                except json.JSONDecodeError as e:
                    logger.error(
                        "Invalid tool arguments JSON for %s: %s — raw=%s",
                        name,
                        e,
                        args_preview,
                    )
                    tool_errors_this_turn += 1
                    content = format_tool_result_for_llm(
                        tool_failure_payload(
                            f"Invalid tool arguments JSON for '{name}': {e}",
                            extra={"raw_arguments_preview": args_preview},
                        ),
                        tool_name=name,
                    )
                    result_preview = content[:300] + ("..." if len(content) > 300 else "")
                    if verbose:
                        logger.info("Tool result: %s", result_preview)
                    yield AgentEvent(
                        type="tool_end",
                        turn=turn_no,
                        payload={"tool": name, "result_preview": result_preview},
                    )
                    tool_msgs.append(ExaoneMessage(role="tool", content=content, tool_call_id=tid))
                    continue

                if not isinstance(parsed_args, dict):
                    logger.error(
                        "Tool arguments must be a JSON object for %s, got %s",
                        name,
                        type(parsed_args).__name__,
                    )
                    tool_errors_this_turn += 1
                    content = format_tool_result_for_llm(
                        tool_failure_payload(
                            f"Tool arguments must be a JSON object for '{name}', "
                            f"got {type(parsed_args).__name__}",
                            extra={"raw_arguments_preview": args_preview},
                        ),
                        tool_name=name,
                    )
                    result_preview = content[:300] + ("..." if len(content) > 300 else "")
                    if verbose:
                        logger.info("Tool result: %s", result_preview)
                    yield AgentEvent(
                        type="tool_end",
                        turn=turn_no,
                        payload={"tool": name, "result_preview": result_preview},
                    )
                    tool_msgs.append(ExaoneMessage(role="tool", content=content, tool_call_id=tid))
                    continue

                args = normalize_json_string_values(parsed_args)
                args_display = json.dumps(args, ensure_ascii=False)
                if verbose:
                    logger.info("Invoking: `%s` with %s", name, args_display[:200])

                try:
                    result = tool_executor(name, args)
                    if tool_executor_return_indicates_error(result):
                        err_msg = result.get("error") if isinstance(result, dict) else None
                        if err_msg is None and isinstance(result, str):
                            try:
                                parsed = json.loads(result)
                                if isinstance(parsed, dict):
                                    err_msg = parsed.get("error")
                            except Exception:
                                pass
                        logger.error("Tool execution failed: %s — %s", name, err_msg or result)
                        tool_errors_this_turn += 1
                    content = format_tool_result_for_llm(result, tool_name=name)
                except Exception as e:
                    logger.exception("Tool execution failed: %s", name)
                    tool_errors_this_turn += 1
                    content = format_tool_result_for_llm(
                        tool_failure_payload(str(e)),
                        tool_name=name,
                    )

                result_preview = content[:300] + ("..." if len(content) > 300 else "")
                if verbose:
                    logger.info("Tool result: %s", result_preview)
                yield AgentEvent(
                    type="tool_end",
                    turn=turn_no,
                    payload={"tool": name, "result_preview": result_preview},
                )
                tool_msgs.append(ExaoneMessage(role="tool", content=content, tool_call_id=tid))

            state["messages"] = tool_msgs
            state["last_tool_calls"] = None
            if tool_errors_this_turn > 0:
                state["consecutive_tool_errors"] = state.get("consecutive_tool_errors", 0) + tool_errors_this_turn
            else:
                state["consecutive_tool_errors"] = 0
            if state["consecutive_tool_errors"] >= max_consecutive_tool_errors:
                state["error"] = (
                    f"Stopped tool loop after {state['consecutive_tool_errors']} consecutive tool execution "
                    f"errors (limit={max_consecutive_tool_errors})."
                )
                if verbose:
                    logger.info(state["error"])
                yield AgentEvent(type="error", turn=turn_no, payload={"message": state["error"]})
                break
        else:
            # (en) Distinguish two ways the for-loop can exhaust max_turns:
            #   1. INTENDED HAND-OFF — the last assistant message issued tool
            #      calls and every one of them produced a tool result that is
            #      now the trailing message. Small-`max_turns` callers (e.g.
            #      ToolAgent.enrich uses max_turns=1) rely on this: they want
            #      one LLM call + one tool round per loop invocation and drive
            #      the next reasoning step themselves. Flag the state so the
            #      caller can react without inheriting a spurious ERROR.
            #   2. REAL STALL — the loop ran out of turns without ever
            #      producing a tool-call-free assistant message. Keep the
            #      existing ERROR (preserves the previous invariant for
            #      callers that pass a large max_turns).
            # (kr) for-loop가 max_turns를 소진하는 두 경로를 구분한다:
            #   1. 의도된 HAND-OFF — 마지막 assistant가 tool_calls를 만들고
            #      그에 대한 tool 결과가 모두 메시지에 붙은 상태로 종료. 작은
            #      max_turns로 호출하는 caller(예: ToolAgent.enrich는 1)는
            #      "한 번의 LLM 호출 + 한 번의 도구 라운드"를 의도하고 다음
            #      reasoning step을 직접 운전한다. 상태 플래그만 세워 caller가
            #      거짓 ERROR를 떠안지 않게 한다.
            #   2. 실제 STALL — turn이 소진될 때까지 tool_call 없는 assistant
            #      응답이 한 번도 안 나옴. 기존 ERROR 유지(큰 max_turns로
            #      호출하던 caller들의 invariant 보존).
            last_assistant_tool_calls = False
            last_role: str | None = None
            for _msg in reversed(state.get("messages", [])):
                _role = getattr(_msg, "role", None)
                if last_role is None:
                    last_role = _role
                if _role == "assistant":
                    last_assistant_tool_calls = bool(getattr(_msg, "tool_calls", None))
                    break

            intended_handoff = last_assistant_tool_calls and last_role == "tool"

            if intended_handoff:
                state["terminated_after_tool_round"] = True
                if verbose:
                    logger.info(
                        "reason-tool loop: reached max_turns (%d) after a tool "
                        "round; deferring next reasoning turn to caller.",
                        max_turns,
                    )
            elif state.get("error") is None:
                state["error"] = (
                    f"Stopped reason-tool loop: reached max_turns ({max_turns}) "
                    "without a final assistant message without tool calls."
                )
                if verbose:
                    logger.info(state["error"])
                yield AgentEvent(
                    type="error",
                    turn=state.get("turn", 0),
                    payload={"message": state["error"]},
                )

        if verbose:
            logger.info("Finished chain.")

        yield AgentEvent(
            type="run_end",
            turn=state.get("turn", 0),
            payload={
                "final_content": state.get("last_content", ""),
                "messages": state.get("messages", []),
                "turns_used": state.get("turn", 0),
                "error": state.get("error"),
                "total_latency_ms": state.get("total_latency_ms", 0.0),
                "reasoning_content": state.get("last_reasoning_content"),
                "terminated_after_tool_round": state.get(
                    "terminated_after_tool_round", False
                ),
            },
        )

    @staticmethod
    def _iter_single_llm_turn(
        llm: "ExaoneClient",
        messages: list["ExaoneMessage"],
        *,
        options: Any | None = None,
        stream_llm: bool = False,
    ) -> Iterator["AgentEvent"]:
        """(en) Single LLM call (no tool loop). Used for streaming or finalize-style turns.

        (kr) 단일 LLM 호출입니다(tool loop 없음). 스트리밍 또는 finalize 스타일 턴에 사용합니다.
        """
        from exaone.agents.events import AgentEvent
        from exaone.llm import ExaoneGenerateOptions
        from exaone.llm.streaming import stream_chunks_to_response

        opts = options or ExaoneGenerateOptions()
        yield AgentEvent(type="run_start", turn=0, payload={"stream_llm": stream_llm})
        yield AgentEvent(type="turn_start", turn=1, payload={})

        msgs, input_error = ensure_input_within_limit(
            messages, llm, reserved_new_tokens=opts.max_new_tokens
        )
        if input_error is not None:
            yield AgentEvent(type="error", turn=1, payload={"message": input_error})
            yield AgentEvent(
                type="run_end",
                turn=0,
                payload={
                    "final_content": "",
                    "messages": msgs,
                    "turns_used": 0,
                    "error": input_error,
                    "total_latency_ms": 0.0,
                },
            )
            return

        input_tokens = estimate_tokens_from_messages(msgs)
        opts = ExaoneGenerateOptions(
            max_new_tokens=cap_max_new_tokens(input_tokens, opts.max_new_tokens),
            temperature=opts.temperature,
            top_p=opts.top_p,
            do_sample=opts.do_sample,
            enable_thinking=opts.enable_thinking,
            tools=opts.tools,
            response_format=getattr(opts, "response_format", None),
        )

        error: str | None = None
        content = ""
        reasoning_content: str | None = None
        latency_ms = 0.0
        try:
            if stream_llm:
                collected: list[Any] = []
                for chunk in llm.chat_stream(msgs, options=opts):
                    collected.append(chunk)
                    if chunk.kind == "text" and chunk.text:
                        yield AgentEvent(
                            type="llm_delta",
                            turn=1,
                            payload={"channel": "content", "text": chunk.text},
                        )
                    elif chunk.kind == "reasoning" and chunk.text:
                        yield AgentEvent(
                            type="llm_delta",
                            turn=1,
                            payload={"channel": "reasoning", "text": chunk.text},
                        )
                    elif chunk.kind == "error":
                        raise RuntimeError(chunk.text or "LLM stream error")
                resp = stream_chunks_to_response(iter(collected))
            else:
                resp = llm.chat(msgs, options=opts)
            content = resp.content or ""
            reasoning_content = getattr(resp, "reasoning_content", None)
            latency_ms = resp.latency_ms or 0.0
        except Exception as e:
            error = str(e)
            yield AgentEvent(type="error", turn=1, payload={"message": error})
        else:
            yield AgentEvent(
                type="llm_end",
                turn=1,
                payload={
                    "content_length": len(content),
                    "reasoning_length": len(reasoning_content or ""),
                    "has_tool_calls": False,
                    "latency_ms": latency_ms,
                },
            )

        yield AgentEvent(
            type="run_end",
            turn=1 if not error else 0,
            payload={
                "final_content": content,
                "messages": msgs,
                "turns_used": 0 if error else 1,
                "error": error,
                "total_latency_ms": latency_ms,
                "reasoning_content": reasoning_content,
            },
        )

    @staticmethod
    def _run_reason_tool_loop(
        llm: "ExaoneClient",
        messages: list["ExaoneMessage"],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_executor: Callable[[str, dict[str, Any]], Any],
        options: Any | None = None,
        max_turns: int = 10,
        max_consecutive_tool_errors: int = 3,
        verbose: bool = False,
        on_event: Callable[["AgentEvent"], None] | None = None,
        stream_llm: bool = False,
        llm_call_phase: str | None = None,
    ) -> _ReasonToolLoopResult:
        """(en) Single-agent for-loop (reason → tool → repeat). Logs turns/tool calls when verbose.

        (kr) 싱글 에이전트 for-loop 기반 루프입니다(reason → tool → 반복). verbose이면 턴/도구 호출을 로깅합니다.
        """
        end_payload: dict[str, Any] = {}
        for ev in BaseAgent._iter_reason_tool_loop(
            llm,
            messages,
            tools=tools,
            tool_executor=tool_executor,
            options=options,
            max_turns=max_turns,
            max_consecutive_tool_errors=max_consecutive_tool_errors,
            verbose=verbose,
            stream_llm=stream_llm,
            llm_call_phase=llm_call_phase,
        ):
            if on_event is not None:
                on_event(ev)
            if ev.type == "run_end":
                end_payload = ev.payload
        return _ReasonToolLoopResult(
            final_content=end_payload.get("final_content", ""),
            messages=end_payload.get("messages", list(messages)),
            turns_used=end_payload.get("turns_used", 0),
            error=end_payload.get("error"),
            total_latency_ms=end_payload.get("total_latency_ms", 0.0),
            terminated_after_tool_round=end_payload.get(
                "terminated_after_tool_round", False
            ),
        )
