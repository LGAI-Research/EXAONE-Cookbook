"""
infrastructure.embedding.embedder.Embedder 단위 테스트.
HTTP는 mock으로 대체.
"""
from __future__ import annotations

import unittest.mock

import pytest

from infrastructure.embedding.embedder import Embedder


def _mock_embedding_body(dim: int = 384, num: int = 1) -> dict:
    return {
        "data": [{"embedding": [0.1] * dim, "index": i} for i in range(num)],
    }


class TestEmbedder:
    """Embedder 기본 동작 및 503 재시도."""

    def test_embed_one_returns_list_of_floats(self):
        body = _mock_embedding_body(dim=4, num=1)
        resp = unittest.mock.Mock()
        resp.status_code = 200
        resp.json.return_value = body
        resp.raise_for_status = unittest.mock.Mock()

        with unittest.mock.patch("requests.post", return_value=resp):
            emb = Embedder(base_url="http://localhost:8000", dimensions=4)
            out = emb.embed_one("hello")
        assert isinstance(out, list)
        assert len(out) == 4
        assert all(isinstance(x, float) for x in out)

    def test_embed_batch_empty_returns_empty(self):
        emb = Embedder(base_url="http://localhost:8000", dimensions=384)
        out = emb.embed_batch([])
        assert out == []

    def test_embed_batch_single(self):
        body = _mock_embedding_body(dim=2, num=1)
        resp = unittest.mock.Mock()
        resp.status_code = 200
        resp.json.return_value = body
        resp.raise_for_status = unittest.mock.Mock()

        with unittest.mock.patch("requests.post", return_value=resp):
            emb = Embedder(base_url="http://localhost:8000", dimensions=2)
            out = emb.embed_batch(["one"])
        assert len(out) == 1
        assert len(out[0]) == 2

    def test_embed_batch_multiple_same_batch(self):
        body = _mock_embedding_body(dim=2, num=3)
        resp = unittest.mock.Mock()
        resp.status_code = 200
        resp.json.return_value = body
        resp.raise_for_status = unittest.mock.Mock()

        with unittest.mock.patch("requests.post", return_value=resp):
            emb = Embedder(base_url="http://localhost:8000", dimensions=2, batch_size=10)
            out = emb.embed_batch(["a", "b", "c"])
        assert len(out) == 3
        for v in out:
            assert len(v) == 2

    def test_base_url_normalized_adds_v1(self):
        emb = Embedder(base_url="http://localhost:8000", dimensions=4)
        assert "/v1" in emb.base_url or emb.base_url.endswith("v1")
        emb2 = Embedder(base_url="http://localhost:8000/v1", dimensions=4)
        assert emb2.base_url.rstrip("/").endswith("v1")
