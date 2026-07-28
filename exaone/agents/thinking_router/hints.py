"""
(en) Prompt helpers for router tool hints.

(kr) router tool hint용 prompt 헬퍼입니다.
"""
from __future__ import annotations

from typing import Any

from exaone.agents.thinking_router.types import RoutePlan


def tool_names_from_schemas(tools: list[dict[str, Any]]) -> list[str]:
    """(en) Extract OpenAI-style tool function names from schema list.

    (kr) schema 목록에서 OpenAI 스타일 tool function 이름을 추출합니다.
    """
    return [
        (t.get("function") or {}).get("name")
        for t in tools
        if (t.get("function") or {}).get("name")
    ]


def append_router_tool_hints(
    system_prompt: str,
    route_plan: RoutePlan,
    *,
    hints_header: str,
) -> str:
    """(en) Append planner tool hints to the system prompt.

    (kr) planner tool hint를 system prompt에 덧붙입니다.
    """
    if route_plan.answerable is False:
        return system_prompt
    if not route_plan.tool_hints:
        return system_prompt
    hint_lines = [
        f"- tool: {hint.name}, arguments: {hint.arguments}, reason: {hint.reason or 'n/a'}"
        for hint in route_plan.tool_hints[:2]
    ]
    return (
        system_prompt
        + f"\n\n{hints_header}\n"
        + "\n".join(hint_lines)
    )
