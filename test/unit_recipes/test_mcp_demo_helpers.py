"""
recipes/track03_tools_and_mcp/mcp_demo server-side helper unit tests.
"""
from __future__ import annotations

import asyncio
import unittest.mock

from exaone.tools.tool_result import ToolResult
from _helpers import (
    coerce_search_result_to_dict,
    compose_web_search_result,
    measure_source_latency,
    parse_citations_from_results,
)
from schemas import (
    CitationItem,
    SourceHealth,
    WebSearchResult,
)


def _ok(source: str, content: str) -> ToolResult:
    return ToolResult.success(content=content, source=source)


def _empty(source: str, reason: str) -> ToolResult:
    return ToolResult.empty(source=source, reason=reason)


def _fail(source: str, error: str) -> ToolResult:
    return ToolResult.failure(source=source, error=error)


class TestComposeWebSearchResult:
    def test_both_fail_returns_ok_false(self):
        r = compose_web_search_result(
            _fail("context7", "network"),
            _fail("duckduckgo", "timeout"),
        )
        assert isinstance(r, WebSearchResult)
        assert r.ok is False
        assert r.sources_used == []
        assert set(r.sources_failed) == {"context7", "duckduckgo"}
        assert r.sources_empty == []
        assert r.error and "context7=network" in r.error and "duckduckgo=timeout" in r.error
        assert r.content == ""

    def test_only_context7_ok(self):
        r = compose_web_search_result(
            _ok("context7", "[Context7 documentation: react]\nuseState body"),
            _empty("duckduckgo", "no results"),
        )
        assert r.ok is True
        assert r.sources_used == ["context7"]
        assert r.sources_empty == ["duckduckgo"]
        assert "useState body" in r.content

    def test_only_ddg_ok(self):
        r = compose_web_search_result(
            _empty("context7", "no matching library"),
            _ok("duckduckgo", "[DuckDuckGo search results]\n1. Title\n   https://x\n   body"),
        )
        assert r.ok is True
        assert r.sources_used == ["duckduckgo"]
        assert r.sources_empty == ["context7"]
        assert "Title" in r.content

    def test_both_ok_concatenates(self):
        r = compose_web_search_result(
            _ok("context7", "CTX_TEXT"),
            _ok("duckduckgo", "DDG_TEXT"),
        )
        assert r.ok is True
        assert r.sources_used == ["context7", "duckduckgo"]
        assert r.sources_empty == [] and r.sources_failed == []
        assert "CTX_TEXT" in r.content and "DDG_TEXT" in r.content


class TestParseCitationsFromResults:
    def test_empty_input_returns_empty(self):
        assert parse_citations_from_results({}) == []
        assert parse_citations_from_results({"content": ""}) == []
        assert parse_citations_from_results({"content": "   "}) == []

    def test_non_dict_returns_empty(self):
        assert parse_citations_from_results("not a dict") == []  # type: ignore[arg-type]

    def test_ddg_block_parses_items(self):
        content = (
            "[DuckDuckGo search results]\n"
            "1. Hello Title\n"
            "   https://example.com/a\n"
            "   first body snippet here\n"
            "2. Second\n"
            "   https://example.com/b\n"
            "   second body\n"
        )
        citations = parse_citations_from_results({"content": content})
        assert len(citations) == 2
        assert citations[0].title == "Hello Title"
        assert citations[0].url == "https://example.com/a"
        assert citations[0].provider == "duckduckgo"
        assert citations[0].snippet and "first body" in citations[0].snippet
        assert citations[1].title == "Second"

    def test_context7_block_yields_one_citation(self):
        content = "[Context7 documentation: react]\nuseState body text"
        citations = parse_citations_from_results({"content": content})
        assert len(citations) == 1
        item = citations[0]
        assert isinstance(item, CitationItem)
        assert item.provider == "context7"
        assert item.url is None
        assert item.title == "Context7: react"
        assert item.snippet and "useState" in item.snippet

    def test_mixed_blocks(self):
        content = (
            "[Context7 documentation: react]\n"
            "react body\n"
            "[DuckDuckGo search results]\n"
            "1. T\n"
            "   https://x\n"
            "   b\n"
        )
        citations = parse_citations_from_results({"content": content})
        providers = [c.provider for c in citations]
        assert "context7" in providers
        assert "duckduckgo" in providers


class TestCoerceSearchResultToDict:
    def test_json_dict_round_trip(self):
        import json

        out = coerce_search_result_to_dict(json.dumps({"ok": True, "content": "x"}))
        assert out == {"ok": True, "content": "x"}

    def test_plain_text_wrapped_in_content(self):
        out = coerce_search_result_to_dict("not json")
        assert out == {"content": "not json"}

    def test_empty_string_returns_empty_dict(self):
        assert coerce_search_result_to_dict("") == {}
        assert coerce_search_result_to_dict("   ") == {}

    def test_non_string_returns_empty_dict(self):
        assert coerce_search_result_to_dict(None) == {}  # type: ignore[arg-type]
        assert coerce_search_result_to_dict(123) == {}  # type: ignore[arg-type]

    def test_json_non_dict_falls_back_to_content(self):
        # JSON array는 dict가 아니므로 raw 문자열을 content로 감싼다.
        out = coerce_search_result_to_dict("[1, 2, 3]")
        assert out == {"content": "[1, 2, 3]"}


class TestMeasureSourceLatency:
    def test_success_marks_has_results_true(self):
        async def fake_fetcher(query: str) -> ToolResult:
            return _ok("context7", "ok")

        h = asyncio.run(measure_source_latency(fake_fetcher, "ping"))
        assert isinstance(h, SourceHealth)
        assert h.available is True
        assert h.has_results is True
        assert h.error is None
        assert h.latency_ms is not None and h.latency_ms >= 0

    def test_no_results_keeps_transport_available(self):
        # transport는 OK인데 결과만 0건인 경우.
        async def fake_fetcher(query: str) -> ToolResult:
            return _empty("duckduckgo", "no results")

        h = asyncio.run(measure_source_latency(fake_fetcher, "ping"))
        assert h.available is True
        assert h.has_results is False
        assert h.error == "no results"

    def test_transport_error_marks_unavailable(self):
        async def fake_fetcher(query: str) -> ToolResult:
            return _fail("duckduckgo", "http error: 503")

        h = asyncio.run(measure_source_latency(fake_fetcher, "ping"))
        assert h.available is False
        assert h.has_results is None
        assert h.error and "503" in h.error

    def test_exception_is_caught_as_transport_failure(self):
        async def fake_fetcher(query: str) -> ToolResult:
            raise RuntimeError("network down")

        h = asyncio.run(measure_source_latency(fake_fetcher, "ping"))
        assert h.available is False
        assert h.has_results is None
        assert h.error and "network down" in h.error


class TestServerToolFunctions:
    """server.py의 tool 함수가 helper와 같은 결과를 반환하는지 wiring 검증."""

    def test_web_search_tool_uses_compose_helper(self):
        """`web_search` tool은 fetcher 결과를 compose_web_search_result로 통합한다."""
        import server as server_mod

        async def fake_ctx7(query, library_hint="python"):
            return _ok("context7", "CTX")

        async def fake_ddg(query, max_results=5):
            return _ok("duckduckgo", "DDG")

        with unittest.mock.patch.object(server_mod, "afetch_context7_for_query", fake_ctx7), \
             unittest.mock.patch.object(server_mod, "afetch_duckduckgo_for_query", fake_ddg):
            result = asyncio.run(server_mod.web_search(query="x"))
        assert isinstance(result, WebSearchResult)
        assert result.ok is True
        assert result.sources_used == ["context7", "duckduckgo"]

    def test_extract_sources_tool_accepts_json_string(self):
        import server as server_mod
        import json

        payload = json.dumps({"content": "[Context7 documentation: react]\nbody"})
        result = server_mod.extract_sources(search_result_json=payload)
        assert result.ok is True
        assert len(result.sources) == 1
        assert result.sources[0].provider == "context7"

    def test_extract_sources_tool_accepts_plain_text(self):
        import server as server_mod

        # JSON이 아닌 plain content 문자열도 그대로 받아 파싱한다.
        result = server_mod.extract_sources(
            search_result_json="[Context7 documentation: react]\nbody"
        )
        assert result.ok is True
        assert len(result.sources) == 1

    def test_extract_sources_empty_input_marks_note(self):
        import server as server_mod

        result = server_mod.extract_sources(search_result_json="")
        assert result.ok is False
        assert result.note and "no citations" in result.note


class TestClientAdapterPreservesStructured:
    """call_tool_result_to_dict 가 structuredContent 전체를 봉투에 보존하는지(왕복) 검증."""

    def test_structured_extras_survive(self):
        import json
        from types import SimpleNamespace

        from client_adapter import call_tool_result_to_dict

        structured = {
            "ok": True,
            "content": "[DuckDuckGo search results] ...",
            "sources_used": ["duckduckgo"],
            "sources_empty": ["context7"],
        }
        fake = SimpleNamespace(structuredContent=structured, content=[], isError=False)
        out = call_tool_result_to_dict(fake)

        # content 는 구조화 전체의 직렬화 → 파싱하면 모든 필드 복원 (예전엔 유실 → None)
        parsed = json.loads(out["content"])
        assert parsed["sources_used"] == ["duckduckgo"]
        assert parsed["sources_empty"] == ["context7"]
        # 봉투는 표준 6필드 유지 (별도 키 추가 없음)
        assert set(out.keys()) == {"ok", "outcome", "content", "source", "error", "metadata"}
        assert out["ok"] is True
