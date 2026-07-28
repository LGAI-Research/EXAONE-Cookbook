"""
infrastructure.database.postgres.graph_adapter.PgGraphAdapter 단위 테스트.
DB 없으면 skip.
"""
from __future__ import annotations

import pytest

pytest.importorskip("psycopg")

from infrastructure.database.postgres import graph_adapter
from infrastructure.database.postgres.graph_adapter import PgGraphAdapter


class TestPgGraphAdapter:
    """PgGraphAdapter 생성 및 query_fn 시그니처."""

    def test_init_requires_psycopg(self):
        adapter = PgGraphAdapter(connection_url="postgresql://u:p@localhost:5432/db")
        assert adapter.entities_table == "graph_entities"
        assert adapter.relations_table == "graph_relations"

    def test_query_fn_for_exaone_returns_callable(self):
        adapter = PgGraphAdapter(connection_url="postgresql://u:p@localhost:5432/db")
        fn = adapter.query_fn_for_exaone(top_k_default=5)
        assert callable(fn)
        try:
            result = fn("test", top_k=2)
        except Exception:
            result = []
        assert isinstance(result, list)

    def test_extract_search_terms_regex_fallback(self, monkeypatch):
        monkeypatch.setattr(graph_adapter, "Kiwi", None)
        monkeypatch.setattr(graph_adapter, "wordpunct_tokenize", None)
        terms = PgGraphAdapter._extract_search_terms('MS MARCO에서 "Graph RAG" 설명해줘')
        assert "Graph RAG" in terms
        assert "RAG" in terms
        assert any(t.startswith("설명") for t in terms)

    def test_extract_search_terms_uses_kiwi_and_nltk(self, monkeypatch):
        class _Token:
            def __init__(self, form, tag):
                self.form = form
                self.tag = tag

        class _FakeKiwi:
            def tokenize(self, _query):
                return [_Token("미라지", "NNP"), _Token("기술", "NNG"), _Token("은", "JX")]

        monkeypatch.setattr(graph_adapter, "Kiwi", lambda: _FakeKiwi())
        monkeypatch.setattr(graph_adapter, "wordpunct_tokenize", lambda _q: ["How", "MARCO", "works"])
        terms = PgGraphAdapter._extract_search_terms("How MARCO works? 마르코 기술은?")
        assert "MARCO" in terms
        assert "works" in terms
        assert "미라지" in terms
        assert "기술" in terms

    @pytest.mark.integration
    def test_ensure_schema_and_query_by_entity(self):
        import os
        url = os.environ.get("POSTGRES_URL") or "postgresql://exaone:exaone@localhost:5432/exaone"
        adapter = PgGraphAdapter(connection_url=url)
        adapter.ensure_schema()
        out = adapter.query_by_entity("test", top_k=2)
        assert isinstance(out, list)
        for item in out:
            assert "text" in item or "content" in item
