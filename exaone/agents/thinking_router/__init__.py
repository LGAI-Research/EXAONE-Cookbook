"""
(en) ThinkingRouter package: classify axes, plan enrich, plan finalize.

Per-turn enrich progress lives in :mod:`exaone.agents.next_step_planner`.

(kr) ThinkingRouter 패키지입니다. 축 분류, enrich 계획, finalize 계획을 수행합니다.

턴별 enrich progress는 :mod:`exaone.agents.next_step_planner`에 있습니다.
"""
from exaone.agents.thinking_router.hints import append_router_tool_hints, tool_names_from_schemas
from exaone.agents.thinking_router.router import ThinkingRouter
from exaone.agents.thinking_router.schemas import (
    CLASSIFY_JSON_SCHEMA,
    CLASSIFY_RESPONSE_FORMAT,
    FINALIZE_JSON_SCHEMA,
    FINALIZE_RESPONSE_FORMAT,
    PLAN_JSON_SCHEMA,
    PLAN_RESPONSE_FORMAT,
    ROUTER_OUTPUT_FORMAT,
    UNIFIED_PLAN_JSON_SCHEMA,
    UNIFIED_PLAN_RESPONSE_FORMAT,
)
from exaone.agents.thinking_router.types import (
    FinalizePlan,
    RouteContext,
    RouteDecision,
    RoutePhase,
    RoutePlan,
    SemanticIntent,
    ToolCallHint,
)

__all__ = [
    "ThinkingRouter",
    "SemanticIntent",
    "RouteDecision",
    "RouteContext",
    "RoutePlan",
    "RoutePhase",
    "FinalizePlan",
    "ToolCallHint",
    "ROUTER_OUTPUT_FORMAT",
    "CLASSIFY_JSON_SCHEMA",
    "CLASSIFY_RESPONSE_FORMAT",
    "PLAN_JSON_SCHEMA",
    "PLAN_RESPONSE_FORMAT",
    "FINALIZE_JSON_SCHEMA",
    "FINALIZE_RESPONSE_FORMAT",
    "UNIFIED_PLAN_JSON_SCHEMA",
    "UNIFIED_PLAN_RESPONSE_FORMAT",
    "append_router_tool_hints",
    "tool_names_from_schemas",
]
