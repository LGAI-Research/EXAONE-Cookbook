#!/usr/bin/env python3
"""
exaone-web-search MCP server.

stdio transport. tools 3개:
- `web_search` — Context7 docs + DuckDuckGo web search 병렬 조회 통합 결과.
- `source_diagnostics` — Context7/DDG 사용 가능 여부, latency, API key 상태 진단.
- `extract_sources` — `web_search` 결과 dict에서 citation 구조화 추출.

각 tool 함수는 Pydantic `BaseModel`을 return type으로 선언해 SDK가 자동으로
structured tool output(`CallToolResult.structuredContent`)으로 직렬화하도록 한다.

LLM 호출은 하지 않는다. server는 검색·진단·추출 컨텍스트 제공자 역할만.

Run (Track 03 notebook spawns the same script)::

    python recipes/track03_tools_and_mcp/mcp_demo/server.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_DEMO_DIR = Path(__file__).resolve().parent
ROOT = _DEMO_DIR.parents[2]  # repo root (recipes/track03/.../mcp_demo)
for _p in (ROOT, _DEMO_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from _helpers import (  # noqa: E402
    coerce_search_result_to_dict,
    compose_web_search_result,
    measure_source_latency,
    parse_citations_from_results,
)
from context7_client import (  # noqa: E402
    afetch_context7_for_query,
    get_context7_api_key,
)
from duckduckgo_client import (  # noqa: E402
    afetch_duckduckgo_for_query,
)
from schemas import (  # noqa: E402
    ExtractSourcesResult,
    SourceDiagnosticsResult,
    WebSearchResult,
)

mcp = FastMCP("exaone-web-search")


@mcp.tool()
async def web_search(
    query: str,
    library_hint: str = "python",
    max_results: int = 5,
) -> WebSearchResult:
    """Context7 docs + DuckDuckGo web search를 병렬 조회한 통합 결과를 반환한다."""
    ctx7, ddg = await asyncio.gather(
        afetch_context7_for_query(query, library_hint=library_hint),
        afetch_duckduckgo_for_query(query, max_results=max_results),
    )
    return compose_web_search_result(ctx7, ddg)


@mcp.tool()
async def source_diagnostics(query: str = "ping") -> SourceDiagnosticsResult:
    """Context7 / DuckDuckGo 사용 가능 여부, latency, API key 설정 상태를 진단한다."""
    ctx7_health, ddg_health = await asyncio.gather(
        measure_source_latency(afetch_context7_for_query, query),
        measure_source_latency(afetch_duckduckgo_for_query, query, max_results=1),
    )
    return SourceDiagnosticsResult(
        ok=ctx7_health.available or ddg_health.available,
        context7=ctx7_health,
        duckduckgo=ddg_health,
        context7_api_key_configured=bool(get_context7_api_key()),
    )


@mcp.tool()
def extract_sources(search_result_json: str) -> ExtractSourcesResult:
    """
    `web_search` 결과(JSON 문자열 또는 `content` 텍스트)에서 citation을 구조화 추출한다.

    LLM이 직접 dict를 다시 인자로 채우기 어렵기 때문에 입력은 string 하나로 통일한다:
    - `web_search` 결과의 JSON 문자열을 그대로 넣어도 되고,
    - `content` 텍스트만 넣어도 동일하게 동작한다.
    """
    coerced = coerce_search_result_to_dict(search_result_json)
    citations = parse_citations_from_results(coerced)
    note = None if citations else "no citations parsed from input"
    return ExtractSourcesResult(ok=bool(citations), sources=citations, note=note)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
