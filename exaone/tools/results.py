"""
(en) Tool execution results and failure payloads.

Custom tool_executor: on failure raise an exception or return tool_failure_payload().
A generic LLM-only error {"error": "..."} is enough and does not count toward consecutive-failure limits.

LLM tool messages use format_tool_result_for_llm() with a <tool_result> wrapper (mitigates prompt injection).

(kr) 도구 실행 결과·실패 payload 모듈이다.

커스텀 tool_executor는 실패 시 예외를 던지거나 tool_failure_payload()를 반환한다.
LLM에만 보여줄 일반 오류는 {"error": "..."}만으로 충분하며 연속 실패 한도에는 잡히지 않는다.

LLM tool 메시지에는 format_tool_result_for_llm()으로 <tool_result> 래퍼를 쓴다(prompt injection 완화).
"""
from __future__ import annotations

import json
from typing import Any

from exaone.context_management import sanitize_untrusted_reference_text

TOOL_FAILURE_MARKER = "_exaone_tool_failure"

DEFAULT_TOOL_FAILURE_GUIDANCE = (
    "Tool execution failed. Check tool name and arguments, "
    "then either retry once with corrected arguments or choose another tool."
)


def tool_failure_payload(
    message: str,
    *,
    guidance: str | None = DEFAULT_TOOL_FAILURE_GUIDANCE,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    (en) Return on tool failure; counts toward max_consecutive_tool_errors.

    (kr) 도구 실패 시 반환하며 max_consecutive_tool_errors 집계 대상이다.
    """
    out: dict[str, Any] = {
        "error": message,
        TOOL_FAILURE_MARKER: True,
    }
    if guidance:
        out["guidance"] = guidance
    if extra:
        out.update(extra)
    return out


def is_tool_failure_payload(result: Any) -> bool:
    """
    (en) True if a dict result is from tool_failure_payload.

    (kr) dict 반환값이 tool_failure_payload인지 판별한다.
    """
    return isinstance(result, dict) and result.get(TOOL_FAILURE_MARKER) is True


def tool_executor_return_indicates_error(result: Any) -> bool:
    """
    (en) True if tool_executor return value counts as a consecutive tool failure (dict or JSON str).

    (kr) tool_executor 반환값이 연속 도구 오류로 집계할 실패인지 판별한다(dict 또는 JSON str).
    """
    if is_tool_failure_payload(result):
        return True
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except Exception:
            return False
        return is_tool_failure_payload(parsed)
    return False


def tool_failure_payload_json(
    message: str,
    *,
    guidance: str | None = DEFAULT_TOOL_FAILURE_GUIDANCE,
    extra: dict[str, Any] | None = None,
) -> str:
    """
    (en) Serialize tool_failure_payload as a JSON string (for string-returning tool_executor).

    (kr) tool_failure_payload를 JSON 문자열로 직렬화한다(문자열 반환 tool_executor용).
    """
    return json.dumps(
        tool_failure_payload(message, guidance=guidance, extra=extra),
        ensure_ascii=False,
    )


def serialize_tool_result(result: Any) -> str:
    """
    (en) JSON-serialize tool result; strips internal marker _exaone_tool_failure.

    (kr) 도구 결과를 JSON으로 직렬화하며 내부 마커(_exaone_tool_failure)는 제거한다.
    """
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return json.dumps(_strip_tool_failure_marker(parsed), ensure_ascii=False)
        except Exception:
            pass
        return result
    if isinstance(result, dict):
        return json.dumps(_strip_tool_failure_marker(result), ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False)


def _escape_xml_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_tool_result_for_llm(result: Any, *, tool_name: str = "unknown") -> str:
    """
    (en) Format LLM tool-role message with untrusted <tool_result> wrapper and structural sanitize.

    (kr) LLM tool role 메시지를 untrusted <tool_result> 래퍼와 구조적 sanitize로 포맷한다.
    """
    body = sanitize_untrusted_reference_text(serialize_tool_result(result))
    safe_name = _escape_xml_attr(tool_name or "unknown")
    return (
        f'<tool_result tool="{safe_name}" untrusted="true">\n'
        f"{body}\n"
        "</tool_result>"
    )


def _strip_tool_failure_marker(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k != TOOL_FAILURE_MARKER}
