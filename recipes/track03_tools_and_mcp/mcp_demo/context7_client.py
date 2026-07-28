"""
Context7 REST API 클라이언트.

- sync `fetch_context7_for_query(...)` — `httpx.Client` 사용. agentic_system의 sync
  tool executor에서 호출.
- async `afetch_context7_for_query(...)` — `httpx.AsyncClient` 사용. mcp/server.py의
  `web_search` tool에서 DDG와 `asyncio.gather`로 병렬 호출.

라이브러리 **문서** 검색용이다. 일반 웹/최신 정보는 DuckDuckGo 쪽이 적절하다.
CONTEXT7_API_KEY가 없으면 비인증 요청(낮은 rate limit)으로 동작.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from exaone.tools.tool_result import ToolResult

CONTEXT7_BASE = "https://context7.com"
_DEFAULT_TIMEOUT = 15.0
_SOURCE = "context7"


def get_context7_api_key() -> str | None:
    return (os.environ.get("CONTEXT7_API_KEY") or "").strip() or None


def _headers(api_key: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _format_text(library_id: str, text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    return f"[Context7 documentation: {library_id}]\n{text}\n"


def _pick_library_id(libs: list[dict[str, Any]]) -> str | None:
    if not libs:
        return None
    first = libs[0] or {}
    return first.get("id") or first.get("name") or None


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------
def _sync_search(
    client: httpx.Client, library_name: str, query: str, api_key: str | None
) -> list[dict[str, Any]]:
    try:
        r = client.get(
            f"{CONTEXT7_BASE}/api/v2/libs/search",
            params={"libraryName": library_name, "query": query},
            headers=_headers(api_key),
        )
        r.raise_for_status()
        data = r.json() if r.text else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _sync_context(
    client: httpx.Client, library_id: str, query: str, api_key: str | None
) -> str:
    try:
        r = client.get(
            f"{CONTEXT7_BASE}/api/v2/context",
            params={"libraryId": library_id, "query": query, "type": "txt"},
            headers=_headers(api_key),
        )
        r.raise_for_status()
        return (r.text or "").strip()
    except Exception:
        return ""


def fetch_context7_for_query(
    query: str, library_hint: str = "python", timeout: float = _DEFAULT_TIMEOUT
) -> ToolResult:
    """질문에 맞는 Context7 문서 블록을 반환한다."""
    api_key = get_context7_api_key()
    try:
        with httpx.Client(timeout=timeout) as client:
            libs = _sync_search(client, library_hint, query, api_key)
            if not libs and library_hint != "python":
                libs = _sync_search(client, "python", query, api_key)
            lib_id = _pick_library_id(libs)
            if not lib_id:
                return ToolResult.empty(source=_SOURCE, reason="no matching library")
            text = _sync_context(client, lib_id, query, api_key)
    except httpx.HTTPError as exc:
        return ToolResult.failure(source=_SOURCE, error=f"http error: {exc}")
    except Exception as exc:  # noqa: BLE001 — 최종 안전망
        return ToolResult.failure(source=_SOURCE, error=str(exc))

    formatted = _format_text(lib_id, text)
    if not formatted:
        return ToolResult.empty(
            source=_SOURCE,
            reason="empty context",
            metadata={"library_id": lib_id},
        )
    return ToolResult.success(
        content=formatted,
        source=_SOURCE,
        metadata={"library_id": lib_id},
    )


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------
async def _async_search(
    client: httpx.AsyncClient, library_name: str, query: str, api_key: str | None
) -> list[dict[str, Any]]:
    try:
        r = await client.get(
            f"{CONTEXT7_BASE}/api/v2/libs/search",
            params={"libraryName": library_name, "query": query},
            headers=_headers(api_key),
        )
        r.raise_for_status()
        data = r.json() if r.text else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


async def _async_context(
    client: httpx.AsyncClient, library_id: str, query: str, api_key: str | None
) -> str:
    try:
        r = await client.get(
            f"{CONTEXT7_BASE}/api/v2/context",
            params={"libraryId": library_id, "query": query, "type": "txt"},
            headers=_headers(api_key),
        )
        r.raise_for_status()
        return (r.text or "").strip()
    except Exception:
        return ""


async def afetch_context7_for_query(
    query: str, library_hint: str = "python", timeout: float = _DEFAULT_TIMEOUT
) -> ToolResult:
    """Async 버전. run.py에서 DDG와 `asyncio.gather`로 병렬 호출."""
    api_key = get_context7_api_key()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            libs = await _async_search(client, library_hint, query, api_key)
            if not libs and library_hint != "python":
                libs = await _async_search(client, "python", query, api_key)
            lib_id = _pick_library_id(libs)
            if not lib_id:
                return ToolResult.empty(source=_SOURCE, reason="no matching library")
            text = await _async_context(client, lib_id, query, api_key)
    except httpx.HTTPError as exc:
        return ToolResult.failure(source=_SOURCE, error=f"http error: {exc}")
    except Exception as exc:  # noqa: BLE001
        return ToolResult.failure(source=_SOURCE, error=str(exc))

    formatted = _format_text(lib_id, text)
    if not formatted:
        return ToolResult.empty(
            source=_SOURCE,
            reason="empty context",
            metadata={"library_id": lib_id},
        )
    return ToolResult.success(
        content=formatted,
        source=_SOURCE,
        metadata={"library_id": lib_id},
    )


__all__ = [
    "afetch_context7_for_query",
    "fetch_context7_for_query",
    "get_context7_api_key",
]
