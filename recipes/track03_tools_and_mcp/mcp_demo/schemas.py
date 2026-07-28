"""
MCP server tool 결과용 Pydantic 모델.

각 모델은 FastMCP `@mcp.tool()`의 return type annotation으로 사용된다.
SDK가 모델을 자동으로 structured tool output(`CallToolResult.structuredContent`)으로
직렬화하므로 클라이언트에서 dict를 안전하게 회수할 수 있다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class WebSearchResult(BaseModel):
    """`web_search` tool envelope."""

    ok: bool
    content: str = ""
    error: str | None = None
    sources_used: list[str] = Field(default_factory=list)
    sources_empty: list[str] = Field(default_factory=list)
    sources_failed: list[str] = Field(default_factory=list)


class SourceHealth(BaseModel):
    """
    단일 source의 상태.

    - `available`: transport(HTTP/네트워크/SDK)가 도달 가능한지.
    - `has_results`: transport는 OK인데 query 결과가 비어 있는지(`True`=결과 있음,
      `False`=결과 0건, `None`=transport 실패라 판단 불가).
    - `latency_ms`: 측정 가능했을 때만 채워짐.
    - `error`: transport 실패 또는 결과 없음 사유 메시지.
    """

    available: bool
    has_results: bool | None = None
    latency_ms: int | None = None
    error: str | None = None


class SourceDiagnosticsResult(BaseModel):
    """`source_diagnostics` tool envelope."""

    ok: bool
    context7: SourceHealth
    duckduckgo: SourceHealth
    context7_api_key_configured: bool


class CitationItem(BaseModel):
    """Citation 한 건."""

    title: str
    url: str | None = None
    provider: str  # "context7" | "duckduckgo"
    snippet: str | None = None


class ExtractSourcesResult(BaseModel):
    """`extract_sources` tool envelope."""

    ok: bool
    sources: list[CitationItem]
    note: str | None = None


__all__ = [
    "CitationItem",
    "ExtractSourcesResult",
    "SourceDiagnosticsResult",
    "SourceHealth",
    "WebSearchResult",
]
