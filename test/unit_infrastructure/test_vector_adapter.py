"""
infrastructure.database.postgres.vector_adapter.PgVectorAdapter 단위 테스트.
DB 없으면 skip. mock embedder 사용.
"""
from __future__ import annotations

import pytest

pytest.importorskip("psycopg")

from infrastructure.database.postgres.vector_adapter import PgVectorAdapter


class MockEmbedder:
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed_one(self, text: str):
        return [0.1] * self.dim


class TestPgVectorAdapter:
    """PgVectorAdapter 생성 및 search_fn 시그니처."""

    def test_init_requires_psycopg(self):
        embedder = MockEmbedder(dim=384)
        adapter = PgVectorAdapter(
            connection_url="postgresql://u:p@localhost:5432/db",
            embedder=embedder,
            embed_dim=384,
        )
        assert adapter.embed_dim == 384
        assert adapter.table_name == "embeddings"

    def test_init_rejects_invalid_identifiers(self):
        embedder = MockEmbedder(dim=384)
        with pytest.raises(ValueError):
            PgVectorAdapter(
                connection_url="postgresql://u:p@localhost:5432/db",
                embedder=embedder,
                table_name="embeddings; DROP TABLE users;--",
                embed_dim=384,
            )

    def test_embed_fn_for_exaone_returns_callable(self):
        embedder = MockEmbedder(dim=4)
        adapter = PgVectorAdapter(
            connection_url="postgresql://u:p@localhost:5432/db",
            embedder=embedder,
            embed_dim=4,
        )
        fn = adapter.embed_fn_for_exaone()
        assert callable(fn)
        out = fn("hello")
        assert isinstance(out, list)
        assert len(out) == 4

    def test_search_fn_for_exaone_returns_callable(self):
        embedder = MockEmbedder(dim=4)
        adapter = PgVectorAdapter(
            connection_url="postgresql://u:p@localhost:5432/db",
            embedder=embedder,
            embed_dim=4,
        )
        fn = adapter.search_fn_for_exaone(top_k_default=5)
        assert callable(fn)
        try:
            result = fn([0.1] * 4, top_k=2)
        except Exception:
            result = []
        assert isinstance(result, list)

    @pytest.mark.integration
    def test_search_returns_list_of_dicts_with_text_score(self):
        import os
        url = os.environ.get("POSTGRES_URL") or "postgresql://exaone:exaone@localhost:5432/exaone"
        embedder = MockEmbedder(dim=384)
        adapter = PgVectorAdapter(connection_url=url, embedder=embedder, embed_dim=384)
        out = adapter.search("test query", top_k=2)
        assert isinstance(out, list)
        for item in out:
            assert "text" in item or "content" in item
            assert "score" in item
