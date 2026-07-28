"""
DuckDuckGo 검색 클라이언트. API 키 불필요.

- sync `fetch_duckduckgo_for_query(...)` — `ddgs.DDGS().text(...)` 직접 호출.
- async `afetch_duckduckgo_for_query(...)` — `asyncio.to_thread`로 sync 호출을 감싼다.
  `ddgs` 공개 async API가 버전에 따라 불안정해 thread 래핑 쪽이 더 안전.

transport 실패는 `failure()`, 결과 0건은 Policy B `empty()`(ok=True)로 구분한다.
"""
from __future__ import annotations

import asyncio
from typing import Any

from exaone.tools.tool_result import ToolResult

_SOURCE = "duckduckgo"

try:  # pragma: no cover — 환경마다 다름
    from ddgs import DDGS as _DDGS  # type: ignore[import-not-found]

    _DDGS_IMPORT_ERROR: str | None = None
except ImportError:
    try:  # pragma: no cover
        from duckduckgo_search import DDGS as _DDGS  # type: ignore[import-not-found]

        _DDGS_IMPORT_ERROR = None
    except ImportError as _exc:  # pragma: no cover
        _DDGS = None  # type: ignore[assignment]
        _DDGS_IMPORT_ERROR = str(_exc)


def _search_sync(query: str, max_results: int) -> list[dict[str, Any]]:
    """DDGS().text 결과를 리스트로 반환. 실패 시 예외 raise."""
    if _DDGS is None:
        raise RuntimeError(f"ddgs 패키지 미설치: {_DDGS_IMPORT_ERROR}")
    return list(_DDGS().text(query, max_results=max_results))


def _format_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return ""
    lines = ["[DuckDuckGo search results]"]
    for i, r in enumerate(results, 1):
        title = r.get("title") or ""
        href = r.get("href") or ""
        body = (r.get("body") or "")[:500]
        lines.append(f"{i}. {title}\n   {href}\n   {body}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------
def fetch_duckduckgo_for_query(query: str, max_results: int = 5) -> ToolResult:
    try:
        results = _search_sync(query, max_results)
    except Exception as exc:  # noqa: BLE001 — 네트워크 에러 전부 흡수
        return ToolResult.failure(source=_SOURCE, error=str(exc))

    formatted = _format_results(results)
    if not formatted:
        return ToolResult.empty(source=_SOURCE, reason="no results")
    return ToolResult.success(
        content=formatted,
        source=_SOURCE,
        metadata={"count": len(results)},
    )


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------
async def afetch_duckduckgo_for_query(query: str, max_results: int = 5) -> ToolResult:
    """`ddgs`를 thread로 off-load해 코루틴에서 await 가능하게 만든다."""
    try:
        results = await asyncio.to_thread(_search_sync, query, max_results)
    except Exception as exc:  # noqa: BLE001
        return ToolResult.failure(source=_SOURCE, error=str(exc))

    formatted = _format_results(results)
    if not formatted:
        return ToolResult.empty(source=_SOURCE, reason="no results")
    return ToolResult.success(
        content=formatted,
        source=_SOURCE,
        metadata={"count": len(results)},
    )


__all__ = [
    "afetch_duckduckgo_for_query",
    "fetch_duckduckgo_for_query",
]
