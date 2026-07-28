"""
MCP client ↔ EXAONE ToolRegistry adapter 계층.

피드백 반영:
- `mcp_tool_to_openai_tool_schema` — MCP `Tool`을 OpenAI/Hermes function-call schema로 변환.
- `call_tool_result_to_dict` — `CallToolResult`에서 `structuredContent` 우선,
  없으면 content blocks 텍스트를 JSON 또는 plain string으로 fallback해 dict 추출.
- `MCPToolExecutor` — sync 진입점에서 async `session.call_tool`을 안전하게 호출.
  ToolRegistry executor는 sync 함수를 기대하므로 `asyncio.run_coroutine_threadsafe`로
  메인 loop에 코루틴을 제출.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from typing import Any

from exaone.config import get_mcp_tool_timeout_s
from exaone.tools.tool_result import ToolResult, ToolResultModel

logger = logging.getLogger(__name__)

# `future.result()`는 코루틴 `wait_for`보다 약간 여유를 둔다 (스레드 스케줄링).
_FUTURE_RESULT_GRACE_S = 2.0


def mcp_tool_to_openai_tool_schema(mcp_tool: Any) -> dict[str, Any]:
    """
    MCP `Tool` 객체(`name`/`description`/`inputSchema`)를 EXAONE ToolRegistry가
    기대하는 OpenAI/Hermes 호환 function-call schema로 변환한다.
    """
    name = getattr(mcp_tool, "name", None) or ""
    description = getattr(mcp_tool, "description", None) or ""
    input_schema = getattr(mcp_tool, "inputSchema", None) or {
        "type": "object",
        "properties": {},
    }
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": input_schema,
        },
    }


def _extract_structured(result: Any) -> dict[str, Any] | None:
    """
    SDK 버전·객체에 따라 structured 필드는 `structuredContent`(camelCase)
    또는 `structured_content`(snake_case)로 노출되며, Pydantic 모델 인스턴스로
    들어올 수도 있다. 셋 다 처리해 dict로 반환.
    """
    for attr in ("structuredContent", "structured_content"):
        val = getattr(result, attr, None)
        if val is None:
            continue
        if isinstance(val, dict) and val:
            return val
        # Pydantic v2 모델
        model_dump = getattr(val, "model_dump", None)
        if callable(model_dump):
            try:
                dumped = model_dump()
            except Exception:  # noqa: BLE001
                dumped = None
            if isinstance(dumped, dict) and dumped:
                return dumped
        # Pydantic v1 호환
        legacy_dict = getattr(val, "dict", None)
        if callable(legacy_dict):
            try:
                dumped = legacy_dict()
            except Exception:  # noqa: BLE001
                dumped = None
            if isinstance(dumped, dict) and dumped:
                return dumped
    return None


def _wrap_structured_payload(structured: dict[str, Any]) -> dict[str, Any]:
    """
    (en) Normalize to the standard 6-field ToolResult envelope, but set ``content`` to the WHOLE
    structured payload serialized to a string — so nothing is dropped: the LLM receives the
    complete tool result, and callers can ``json.loads(content)`` to read fields like sources_used.
    No extra envelope key is added (shape stays 6 fields).

    (kr) 표준 6필드 봉투로 정규화하되 ``content`` 를 구조화 전체의 직렬화 문자열로 채운다 —
    누락 없음: LLM 은 전체 결과를 받고, 호출부는 ``json.loads(content)`` 로 sources_used 등을 읽는다.
    봉투에 별도 키를 추가하지 않는다(6필드 유지).
    """
    envelope = dict(ToolResultModel.validate_payload(structured))
    if isinstance(structured, dict):
        envelope["content"] = json.dumps(structured, ensure_ascii=False)
    return envelope


def call_tool_result_to_dict(result: Any) -> dict[str, Any]:
    """
    `CallToolResult`에서 안전하게 dict를 추출한다.

    1) `structuredContent` / `structured_content` / Pydantic 모델 인스턴스 — 모두 dict로.
    2) 없으면 `content`의 첫 TextContent를 JSON으로 파싱.
    3) JSON 파싱 실패 시 plain text를 success/failure로 감쌈.
    4) 빈 결과: transport OK면 Policy B empty, MCP isError면 failure.
    5) ``ToolResultModel.parse_wire`` (wire 정규화 → Pydantic → dict)로 통일 검증한다.
    """
    if result is None:
        return ToolResult.failure(source="mcp", error="empty result").to_dict()

    structured = _extract_structured(result)
    if structured is not None:
        return _wrap_structured_payload(structured)

    is_error = bool(getattr(result, "isError", False))
    content_blocks = getattr(result, "content", None) or []

    text_parts: list[str] = []
    for block in content_blocks:
        text = getattr(block, "text", None)
        if text:
            text_parts.append(text)
    raw_text = "\n".join(text_parts).strip()

    if not raw_text:
        if is_error:
            payload = ToolResult.failure(source="mcp", error="empty result")
        else:
            payload = ToolResult.empty(source="mcp", reason="empty result")
        return payload.to_dict()

    try:
        parsed = json.loads(raw_text)
    except (TypeError, ValueError):
        if is_error:
            payload = ToolResult.failure(source="mcp", error=raw_text)
        else:
            payload = ToolResult.success(content=raw_text, source="mcp")
        return payload.to_dict()

    if isinstance(parsed, dict):
        return _wrap_structured_payload(parsed)
    if is_error:
        return ToolResult.failure(source="mcp", error=raw_text).to_dict()
    return ToolResult.success(content=raw_text, source="mcp").to_dict()


async def call_tool_with_timeout(
    session: Any,
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    timeout: float | None = None,
) -> Any:
    """
    async `session.call_tool`에 상한을 둔다.

    default/full 모드 공통. `timeout`이 None이면 `.env`의 `MCP_TOOL_TIMEOUT_S`를 쓴다.
    """
    if arguments is None:
        arguments = {}
    if timeout is None:
        timeout = float(get_mcp_tool_timeout_s())
    return await asyncio.wait_for(
        session.call_tool(name, arguments),
        timeout=timeout,
    )


class MCPToolExecutor:
    """
    sync executor 인터페이스로 async `session.call_tool`을 호출하는 래퍼.

    ToolRegistry는 `(name, args) -> dict` sync executor를 기대한다. 이 클래스는
    `asyncio.run_coroutine_threadsafe`로 코루틴을 메인 event loop에 제출한 뒤
    `.result()`로 sync하게 결과를 회수한다. ToolAgent가 별도 thread에서 실행되는
    상황(`asyncio.to_thread(ToolAgent.run)`)을 가정한다.
    """

    def __init__(
        self,
        session: Any,
        loop: asyncio.AbstractEventLoop,
        *,
        timeout: float | None = None,
    ):
        self._session = session
        self._loop = loop
        self._timeout = (
            float(timeout) if timeout is not None else float(get_mcp_tool_timeout_s())
        )
        self.call_count = 0
        # tool 이름별 마지막 호출 결과(dict) — web_search ok 여부 판단에 사용.
        self.last_results: dict[str, dict[str, Any]] = {}

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if arguments is None:
            arguments = {}
        self.call_count += 1
        future = None
        try:
            future = asyncio.run_coroutine_threadsafe(
                call_tool_with_timeout(
                    self._session,
                    name,
                    arguments,
                    timeout=self._timeout,
                ),
                self._loop,
            )
            result = future.result(timeout=self._timeout + _FUTURE_RESULT_GRACE_S)
        except (TimeoutError, concurrent.futures.TimeoutError, asyncio.TimeoutError):
            if future is not None:
                future.cancel()
            logger.warning(
                "MCP call_tool timeout: name=%s timeout=%ss",
                name,
                self._timeout,
            )
            payload = ToolResult.failure(
                source="mcp",
                error=f"MCP call_tool({name}) timed out after {self._timeout}s",
            ).to_dict()
            self.last_results[name] = payload
            return payload
        except Exception as exc:  # noqa: BLE001
            logger.exception("MCP call_tool 실패: name=%s", name)
            payload = ToolResult.failure(
                source="mcp",
                error=f"MCP call_tool({name}) failed: {exc}",
            ).to_dict()
            self.last_results[name] = payload
            return payload
        payload = call_tool_result_to_dict(result)
        self.last_results[name] = payload
        return payload


__all__ = [
    "MCPToolExecutor",
    "call_tool_result_to_dict",
    "call_tool_with_timeout",
    "mcp_tool_to_openai_tool_schema",
    "_extract_structured",
]
