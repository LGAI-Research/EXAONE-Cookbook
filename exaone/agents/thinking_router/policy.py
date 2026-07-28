"""
(en) Classifier axis normalization and product rules.

(kr) classifier 축 정규화 및 제품 규칙입니다.
"""
from __future__ import annotations

from typing import Any

from exaone.agents.thinking_router.constants import TEMP_MIN, TOP_P_DEFAULT
from exaone.agents.thinking_router.schemas import ROUTER_OUTPUT_FORMAT
from exaone.agents.thinking_router.types import RouteContext, RouteDecision, SemanticIntent

_VALID_SEMANTIC = frozenset(e.value for e in SemanticIntent)


def default_axes_dict(ctx: RouteContext) -> dict[str, Any]:
    if ctx.has_tools:
        return {
            "enable_thinking": True,
            "temperature": 1.0,
            "top_p": TOP_P_DEFAULT,
            "semantic_intent": SemanticIntent.GENERAL.value,
        }
    return {
        "enable_thinking": False,
        "temperature": 1.0,
        "top_p": TOP_P_DEFAULT,
        "semantic_intent": SemanticIntent.GENERAL.value,
    }


def apply_policy(axes: dict[str, Any], ctx: RouteContext) -> RouteDecision:
    sem = str(axes.get("semantic_intent", "")).strip().lower()
    if sem not in _VALID_SEMANTIC:
        sem = SemanticIntent.GENERAL.value
    temp = float(axes.get("temperature", 1.0))
    temp = max(TEMP_MIN, min(temp, 2.0))
    top_p = float(axes.get("top_p", TOP_P_DEFAULT))
    top_p = max(0.05, min(top_p, 1.0))
    thinking = bool(axes.get("enable_thinking", False))
    if ctx.has_tools:
        thinking = True
    return RouteDecision(
        enable_thinking=thinking,
        temperature=temp,
        top_p=top_p,
        final_response_format=ROUTER_OUTPUT_FORMAT,
        semantic_intent=sem,
    )


def finalize_decision_from_enrich(
    enrich: RouteDecision,
    *,
    has_context: bool,
) -> RouteDecision:
    """Reuse enrich axes for finalize without a second classify LLM call."""
    ctx = RouteContext(has_tools=False, has_context=has_context)
    return apply_policy(
        {
            "enable_thinking": enrich.enable_thinking,
            "temperature": enrich.temperature,
            "top_p": enrich.top_p,
            "semantic_intent": enrich.semantic_intent,
        },
        ctx,
    )
