"""
(en) ThinkingRouter: classify axes, plan enrich, plan finalize.

(kr) ThinkingRouter입니다. 축 분류, enrich 계획, finalize 계획을 수행합니다.
"""
from __future__ import annotations

import hashlib
from typing import Any

from exaone.agents.base_agent import BaseAgent, ChatHistoryTurn
from exaone.agents.run_trace import AgentRunPhase
from exaone.agents.thinking_router import prompts
from exaone.agents.thinking_router.llm_json import chat_json
from exaone.agents.thinking_router.parsing import parse_json_object, parse_tool_hints
from exaone.agents.thinking_router.policy import (
    apply_policy,
    default_axes_dict,
    finalize_decision_from_enrich,
)
from exaone.agents.thinking_router.schemas import (
    CLASSIFY_RESPONSE_FORMAT,
    FINALIZE_RESPONSE_FORMAT,
    PLAN_RESPONSE_FORMAT,
    UNIFIED_PLAN_RESPONSE_FORMAT,
)
from exaone.agents.thinking_router.types import (
    FinalizePlan,
    RouteContext,
    RouteDecision,
    RoutePhase,
    RoutePlan,
)


class ThinkingRouter:
    """(en) Axis-based RouteDecision for ToolAgent runs.

    (kr) ToolAgent 실행용 축 기반 RouteDecision을 제공합니다.
    """

    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model
        self._route_cache: dict[str, RouteDecision] = {}

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        return parse_json_object(text)

    @staticmethod
    def _route_cache_key(query: str, ctx: RouteContext) -> str:
        history_tail = (ctx.history or [])[-4:]
        hist_key = " | ".join(
            f"{m.get('role', '')}:{m.get('content', '')}" for m in history_tail
        )
        raw = f"{query}\nT={int(ctx.has_tools)}\nC={int(ctx.has_context)}\nH={hist_key}"
        return hashlib.md5(raw.encode()).hexdigest()

    def route(
        self,
        query: str,
        *,
        history: list[ChatHistoryTurn] | None = None,
        has_tools: bool = False,
        has_context: bool = False,
    ) -> RouteDecision:
        normalized = BaseAgent.normalize_chat_history_turns(history)
        ctx = RouteContext(
            history=normalized or None,
            has_tools=has_tools,
            has_context=has_context,
        )
        cache_key = self._route_cache_key(query, ctx)
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]
        axes = self._call_classifier(query, ctx)
        out = apply_policy(axes, ctx)
        self._route_cache[cache_key] = out
        return out

    def plan_enrich(
        self,
        query: str,
        *,
        history: list[ChatHistoryTurn] | None = None,
        has_tools: bool = False,
        has_context: bool = False,
        available_tools: list[str] | None = None,
        default_tool_agent_key: str | None = None,
    ) -> RoutePlan:
        decision = self.route(
            query,
            history=history,
            has_tools=has_tools,
            has_context=has_context,
        )
        tool_agent_key = (default_tool_agent_key or "tool").strip().lower()
        rewritten_query = query
        hints: list[Any] = []
        catalog = [t for t in (available_tools or []) if t]
        if has_tools and catalog:
            planned = self._call_enrich_planner(
                query=query,
                decision=decision,
                has_tools=has_tools,
                has_context=has_context,
                available_tools=catalog,
            )
            if planned is not None:
                tool_agent_key = planned.tool_agent_key or tool_agent_key
                rewritten_query = planned.rewritten_query or query
                hints = planned.tool_hints
        return RoutePlan(
            decision=decision,
            tool_agent_key=tool_agent_key,
            rewritten_query=rewritten_query,
            phase=RoutePhase.ENRICH.value,
            tool_hints=hints,
        )

    def plan_enrich_unified(
        self,
        query: str,
        *,
        history: list[ChatHistoryTurn] | None = None,
        has_tools: bool = False,
        has_context: bool = False,
        available_tools: list[str] | None = None,
        default_tool_agent_key: str | None = None,
    ) -> RoutePlan:
        """Single LLM call: classify axes + catalog answerability + enrich hints.

        Falls back to :meth:`plan_enrich` (classify + planner) when the unified call fails.
        """
        tool_agent_key = (default_tool_agent_key or "tool").strip().lower()
        catalog = [t for t in (available_tools or []) if t]
        if not (has_tools and catalog):
            return self.plan_enrich(
                query,
                history=history,
                has_tools=has_tools,
                has_context=has_context,
                available_tools=available_tools,
                default_tool_agent_key=default_tool_agent_key,
            )
        unified = self._call_unified_enrich_planner(
            query=query,
            has_tools=has_tools,
            has_context=has_context,
            available_tools=catalog,
            default_tool_agent_key=tool_agent_key,
        )
        if unified is not None:
            return unified
        return self.plan_enrich(
            query,
            history=history,
            has_tools=has_tools,
            has_context=has_context,
            available_tools=available_tools,
            default_tool_agent_key=default_tool_agent_key,
        )

    def plan_finalize(
        self,
        query: str,
        *,
        history: list[ChatHistoryTurn] | None = None,
        has_context: bool = False,
        default_answer_tool_agent: str = "answer",
        enrich_decision: RouteDecision | None = None,
    ) -> FinalizePlan:
        """Choose answer style and axes for the tools-off JSON turn.

        When *enrich_decision* is provided (from enrich planning), skips a second
        classify ``route()`` LLM call and re-applies finalize policy locally.
        """
        if enrich_decision is not None:
            decision = finalize_decision_from_enrich(
                enrich_decision,
                has_context=has_context,
            )
        else:
            decision = self.route(
                query,
                history=history,
                has_tools=False,
                has_context=has_context,
            )
        answer_key = default_answer_tool_agent
        rewritten = query
        try:
            raw = chat_json(
                self._client,
                messages=[
                    {"role": "system", "content": prompts.FINALIZE_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"Query: {query}\n"
                            f"has_retrieved_context: {str(has_context).lower()}"
                        ),
                    },
                ],
                max_new_tokens=150,
                response_format=FINALIZE_RESPONSE_FORMAT,
                phase=AgentRunPhase.ROUTE_PLAN_FINALIZE,
            )
            data = parse_json_object(raw)
            answer_key = str(
                data.get("answer_tool_agent_key")
                or data.get("answer_expert_key")
                or answer_key
            ).strip().lower()
            rewritten = str(data.get("rewritten_query") or query)
        except Exception:
            if has_context:
                answer_key = "rag"
        return FinalizePlan(
            decision=decision,
            answer_tool_agent_key=answer_key,
            rewritten_query=rewritten,
        )

    def _call_classifier(self, query: str, ctx: RouteContext) -> dict[str, Any]:
        history_tail = (ctx.history or [])[-4:]
        history_text = "\n".join(
            f"- {m.get('role', 'unknown')}: {str(m.get('content', ''))[:200]}"
            for m in history_tail
        ) or "- (none)"
        classifier_input = (
            f"Query:\n{query}\n\n"
            f"Execution context:\n"
            f"- tools_available: {str(ctx.has_tools).lower()}\n"
            f"- external_context_attached: {str(ctx.has_context).lower()}\n"
            f"- recent_history:\n{history_text}"
        )
        try:
            raw = chat_json(
                self._client,
                messages=[
                    {"role": "system", "content": prompts.CLASSIFY_SYSTEM},
                    *prompts.CLASSIFY_FEWSHOT,
                    {"role": "user", "content": classifier_input},
                ],
                max_new_tokens=200,
                response_format=CLASSIFY_RESPONSE_FORMAT,
                phase=AgentRunPhase.ROUTE_CLASSIFY,
            )
            data = parse_json_object(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return default_axes_dict(ctx)

    def _call_enrich_planner(
        self,
        *,
        query: str,
        decision: RouteDecision,
        has_tools: bool,
        has_context: bool,
        available_tools: list[str],
    ) -> RoutePlan | None:
        planner_input = (
            f"Query: {query}\n"
            f"Context: tools_available={str(has_tools).lower()}, "
            f"evidence_in_thread={str(has_context).lower()}\n"
            f"Available tools: {', '.join(available_tools)}\n"
            f"Semantic intent: {decision.semantic_intent}"
        )
        try:
            raw = chat_json(
                self._client,
                messages=[
                    {"role": "system", "content": prompts.PLAN_SYSTEM},
                    *prompts.PLAN_FEWSHOT,
                    {"role": "user", "content": planner_input},
                ],
                max_new_tokens=300,
                response_format=PLAN_RESPONSE_FORMAT,
                phase=AgentRunPhase.ROUTE_PLAN_ENRICH,
            )
            data = parse_json_object(raw)
            tool_agent_key = str(
                data.get("tool_agent_key")
                or data.get("expert_key")
                or data.get("agent_key")
                or "tool"
            ).strip().lower()
            rewritten_query = str(data.get("rewritten_query") or query)
            parsed_hints = parse_tool_hints(
                data.get("tool_hints") or [],
                available_tools=available_tools,
                default_tool_agent_key=tool_agent_key,
            )
            return RoutePlan(
                decision=decision,
                tool_agent_key=tool_agent_key,
                rewritten_query=rewritten_query,
                tool_hints=parsed_hints,
            )
        except Exception:
            return None

    def _call_unified_enrich_planner(
        self,
        *,
        query: str,
        has_tools: bool,
        has_context: bool,
        available_tools: list[str],
        default_tool_agent_key: str,
    ) -> RoutePlan | None:
        planner_input = (
            f"Query: {query}\n"
            f"Context: tools_available={str(has_tools).lower()}, "
            f"evidence_in_thread={str(has_context).lower()}\n"
            f"Available tools: {', '.join(available_tools)}"
        )
        try:
            raw = chat_json(
                self._client,
                messages=[
                    {"role": "system", "content": prompts.UNIFIED_PLAN_SYSTEM},
                    *prompts.UNIFIED_PLAN_FEWSHOT,
                    {"role": "user", "content": planner_input},
                ],
                max_new_tokens=400,
                response_format=UNIFIED_PLAN_RESPONSE_FORMAT,
                phase=AgentRunPhase.ROUTE_PLAN_ENRICH_UNIFIED,
            )
            data = parse_json_object(raw)
            ctx = RouteContext(has_tools=has_tools, has_context=has_context)
            decision = apply_policy(data, ctx)
            tool_agent_key = str(
                data.get("tool_agent_key")
                or data.get("expert_key")
                or data.get("agent_key")
                or default_tool_agent_key
            ).strip().lower()
            rewritten_query = str(data.get("rewritten_query") or query)
            parsed_hints = parse_tool_hints(
                data.get("tool_hints") or [],
                available_tools=available_tools,
                default_tool_agent_key=tool_agent_key,
            )
            answerable = data.get("answerable")
            if not isinstance(answerable, bool):
                answerable = None
            return RoutePlan(
                decision=decision,
                tool_agent_key=tool_agent_key,
                rewritten_query=rewritten_query,
                phase=RoutePhase.ENRICH.value,
                tool_hints=parsed_hints,
                answerable=answerable,
            )
        except Exception:
            return None
