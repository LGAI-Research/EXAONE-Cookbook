"""
MCP server tool 함수에서 사용하는 순수 helper.

`server.py`의 `@mcp.tool()` 데코레이터 본문은 이 helper들을 그대로 호출합니다.
helper만 단위 테스트하면 데코레이터 내부를 뜯지 않고도 핵심 로직 검증이 가능합니다.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Awaitable, Callable

from exaone.tools.tool_result import ToolResult
from schemas import (
    CitationItem,
    SourceHealth,
    WebSearchResult,
)

_DDG_HEADER = "[DuckDuckGo search results]"
_CONTEXT7_HEADER_PREFIX = "[Context7 documentation: "

# DDG 결과 한 항목: "<n>. <title>\n   <href>\n   <body>"
_DDG_ITEM_RE = re.compile(
    r"^\s*\d+\.\s*(?P<title>.+?)\n\s+(?P<href>\S+)\n\s+(?P<body>.+?)(?=\n\s*\d+\.\s|\Z)",
    re.MULTILINE | re.DOTALL,
)


def compose_web_search_result(ctx7: ToolResult, ddg: ToolResult) -> WebSearchResult:
    """
    Context7와 DuckDuckGo `ToolResult` 두 개를 받아 통합 envelope을 만든다.

    - 두 source 모두 본문 없음(실패·0건)이면 ok=False, error에 둘 다 명시.
    - 한 source라도 본문이 있으면 ok=True, content에 성공 source 텍스트 합성.
    - Policy B: outcome=empty(0건)는 transport OK로 간주하나 본문은 없음.
    """
    parts: list[str] = []
    used: list[str] = []
    empty: list[str] = []
    failed: list[str] = []
    errors: list[str] = []

    for r in (ctx7, ddg):
        if r.has_content:
            parts.append(r.content.strip())
            used.append(r.source)
        elif r.is_empty:
            # (en) Source worked but returned no results — distinct from a failure.
            # (kr) 소스는 정상 동작했으나 결과 0건 — 실패와 구분한다.
            empty.append(r.source)
            errors.append(f"{r.source}={r.metadata.get('empty_reason') or 'empty'}")
        else:
            failed.append(r.source)
            errors.append(f"{r.source}={r.error or 'failed'}")

    if not used:
        return WebSearchResult(
            ok=False,
            error="; ".join(errors) if errors else "no sources available",
            sources_used=[],
            sources_empty=empty,
            sources_failed=failed,
        )

    return WebSearchResult(
        ok=True,
        content="\n\n".join(parts),
        sources_used=used,
        sources_empty=empty,
        sources_failed=failed,
    )


def coerce_search_result_to_dict(search_result_json: str) -> dict[str, Any]:
    """
    `extract_sources` tool 입력을 안전하게 dict로 변환.

    LLM이 `web_search` 결과 dict를 그대로 다시 인자로 넣어 호출하기는 어렵기
    때문에, tool 인터페이스는 string 한 개만 받는다. 이 함수는:

    1) 입력이 JSON 문자열이면 파싱해 dict로 사용.
    2) 파싱 실패하거나 dict가 아니면 입력 자체를 `{"content": <raw>}`로 감싼다.
       (citation 파서가 `content` 키를 보므로 plain text도 자연스럽게 처리됨.)
    """
    if not isinstance(search_result_json, str):
        return {}
    text = search_result_json.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return {"content": text}
    if isinstance(parsed, dict):
        return parsed
    return {"content": text}


def parse_citations_from_results(search_result: dict) -> list[CitationItem]:
    """
    `web_search` 결과 dict의 content 텍스트에서 citation을 구조화 추출.

    - DDG 블록(`[DuckDuckGo search results]\\n1. <title>\\n   <href>\\n   <body>...`)에서
      title/url/snippet 파싱.
    - Context7 블록(`[Context7 documentation: <library_id>]\\n<text>`)은 한 항목으로.
    """
    if not isinstance(search_result, dict):
        return []
    content = (search_result.get("content") or "").strip()
    if not content:
        return []

    citations: list[CitationItem] = []
    sections = _split_into_sections(content)

    for section in sections:
        section = section.strip()
        if not section:
            continue
        if section.startswith(_CONTEXT7_HEADER_PREFIX):
            header_end = section.find("]\n")
            if header_end == -1:
                continue
            library_id = section[len(_CONTEXT7_HEADER_PREFIX):header_end]
            body = section[header_end + 2:].strip()
            citations.append(
                CitationItem(
                    title=f"Context7: {library_id}",
                    url=None,
                    provider="context7",
                    snippet=body[:500] if body else None,
                )
            )
        elif section.startswith(_DDG_HEADER):
            body = section[len(_DDG_HEADER):].strip()
            for m in _DDG_ITEM_RE.finditer(body + "\n"):
                citations.append(
                    CitationItem(
                        title=m.group("title").strip(),
                        url=m.group("href").strip() or None,
                        provider="duckduckgo",
                        snippet=m.group("body").strip()[:500] or None,
                    )
                )
    return citations


def _split_into_sections(content: str) -> list[str]:
    """`[DuckDuckGo search results]` / `[Context7 documentation: ...]` 헤더 단위로 분리."""
    sections: list[str] = []
    buf: list[str] = []
    for line in content.split("\n"):
        if line.startswith(_DDG_HEADER) or line.startswith(_CONTEXT7_HEADER_PREFIX):
            if buf:
                sections.append("\n".join(buf))
                buf = []
        buf.append(line)
    if buf:
        sections.append("\n".join(buf))
    return sections


async def measure_source_latency(
    fetcher: Callable[..., Awaitable[ToolResult]],
    query: str,
    **fetcher_kwargs,
) -> SourceHealth:
    """
    단일 source의 transport 도달성과 결과 유무를 분리해 보고한다.

    - 예외 발생 → `available=False`, `has_results=None`(판단 불가), `error=<예외 메시지>`.
    - `outcome=success` → `available=True`, `has_results=True`.
    - `outcome=empty` (Policy B, transport OK·0건) → `available=True`, `has_results=False`.
    - 그 외 실패 → `available=False`, `has_results=None`.

    fetcher는 async callable이며 ToolResult를 반환해야 한다.
    """
    start = time.perf_counter()
    try:
        result = await fetcher(query, **fetcher_kwargs)
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return SourceHealth(
            available=False,
            has_results=None,
            latency_ms=elapsed_ms,
            error=str(exc),
        )
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    if result.has_content:
        return SourceHealth(
            available=True,
            has_results=True,
            latency_ms=elapsed_ms,
            error=None,
        )
    if result.is_empty:
        return SourceHealth(
            available=True,
            has_results=False,
            latency_ms=elapsed_ms,
            error=str(result.metadata.get("empty_reason") or "no results"),
        )
    return SourceHealth(
        available=False,
        has_results=None,
        latency_ms=elapsed_ms,
        error=result.error or "transport failure",
    )


__all__ = [
    "coerce_search_result_to_dict",
    "compose_web_search_result",
    "measure_source_latency",
    "parse_citations_from_results",
]
