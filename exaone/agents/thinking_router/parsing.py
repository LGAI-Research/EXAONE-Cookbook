"""
(en) JSON parsing and tool-hint normalization for ThinkingRouter.

(kr) ThinkingRouter용 JSON 파싱 및 tool-hint 정규화입니다.
"""
from __future__ import annotations

import json
from typing import Any

from exaone.agents.thinking_router.types import ToolCallHint


def parse_json_object(text: str) -> dict[str, Any]:
    """(en) Best-effort JSON object parse; tolerate extra whitespace around a single object,
    then fall back to deterministic repair for truncated/corrupted model JSON.

    (kr) best-effort JSON object 파싱입니다. 단일 object 주변의 여분 공백을 허용하고,
    잘리거나 손상된 모델 JSON 은 결정적 복구로 한 번 더 시도합니다.
    """
    s = (text or "").strip()
    if "{" in s and "}" in s:
        start = s.find("{")
        end = s.rfind("}")
        s = s[start : end + 1]
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # (en) Reuse the structured-output AutoRepair (brackets / unclosed string / trailing
        #      truncation) on the isolated object before giving up. We call .repair() (not
        #      .process()) so a broken object is rebuilt instead of collapsing to a valid
        #      inner array; lazy import avoids an import cycle.
        # (kr) 포기 전에 구조화 출력용 AutoRepair(괄호/미닫힌 문자열/끝부분 잘림)를 분리된
        #      object 에 재사용한다. .process() 가 아니라 .repair() 를 써서 깨진 object 가
        #      내부 배열로 떨어지지 않고 object 로 복구되게 한다. 지연 import 로 순환을 피한다.
        from exaone.output.auto_repair import AutoRepair

        repaired = AutoRepair().repair(s)
        if repaired.success and isinstance(repaired.data, dict):
            return repaired.data
        raise


def parse_tool_hints(
    items: Any,
    *,
    available_tools: list[str],
    default_tool_agent_key: str,
    max_hints: int = 2,
) -> list[ToolCallHint]:
    from exaone.agents.tool_agent_catalog import normalize_api_tool_name

    catalog = set(available_tools)
    parsed: list[ToolCallHint] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        api_name = normalize_api_tool_name(name, default_tool_agent_key=default_tool_agent_key)
        if api_name not in catalog:
            continue
        name = api_name
        args = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
        reason = str(item.get("reason") or "")
        parsed.append(ToolCallHint(name=name, arguments=args, reason=reason))
    return parsed[:max_hints]
