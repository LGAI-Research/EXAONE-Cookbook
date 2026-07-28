"""
(en) ThinkingRouter domain types.

(kr) ThinkingRouter 도메인 타입입니다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from exaone.agents.thinking_router.constants import TOP_P_DEFAULT


class SemanticIntent(str, Enum):
    """(en) Soft label for logging and planner hints only.

    (kr) 로깅 및 planner hint 전용의 소프트 라벨입니다.
    """

    ANALYTICAL = "analytical"
    STRUCTURED = "structured"
    GENERAL = "general"


@dataclass
class RouteDecision:
    """(en) Router output: orthogonal knobs for downstream agents.

    (kr) Router 출력입니다. 하위 agent용 직교 knob를 담습니다.
    """

    enable_thinking: bool
    temperature: float
    top_p: float = TOP_P_DEFAULT
    final_response_format: dict[str, Any] = field(default_factory=dict)
    semantic_intent: str = SemanticIntent.GENERAL.value


@dataclass
class RouteContext:
    """(en) Execution context for the classifier.

    (kr) classifier용 실행 컨텍스트입니다.
    """

    history: list[dict[str, str]] | None = None
    has_tools: bool = False
    has_context: bool = False


@dataclass
class ToolCallHint:
    """(en) Planner output for tool-call guidance.

    (kr) tool-call 가이드용 planner 출력입니다.
    """

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class RoutePhase(str, Enum):
    ENRICH = "enrich"
    FINALIZE = "finalize"


@dataclass
class FinalizePlan:
    """(en) Finalize-phase routing: which ToolAgent prompt style for the final JSON turn.

    (kr) finalize 단계 라우팅입니다. 최종 JSON 턴에 사용할 ToolAgent prompt 스타일을 결정합니다.
    """

    decision: RouteDecision
    answer_tool_agent_key: str = "answer"
    rewritten_query: str = ""


@dataclass
class RoutePlan:
    """(en) Enrich-phase routing + execution hints for ToolAgent.

    (kr) enrich 단계 라우팅과 ToolAgent 실행 hint입니다.
    """

    decision: RouteDecision
    tool_agent_key: str
    rewritten_query: str
    phase: str = RoutePhase.ENRICH.value
    tool_hints: list[ToolCallHint] = field(default_factory=list)
    answer_tool_agent_key: str = "answer"
    answerable: bool | None = None

    @property
    def agent_key(self) -> str:
        return self.tool_agent_key


def default_route_decision(*, has_tools: bool) -> RouteDecision:
    """(en) Fallback axes when classifier LLM call fails.

    (kr) classifier LLM 호출 실패 시 사용하는 fallback 축입니다.
    """
    from exaone.agents.thinking_router.schemas import ROUTER_OUTPUT_FORMAT

    return RouteDecision(
        enable_thinking=has_tools,
        temperature=1.0,
        top_p=TOP_P_DEFAULT,
        final_response_format=ROUTER_OUTPUT_FORMAT,
        semantic_intent=SemanticIntent.GENERAL.value,
    )
