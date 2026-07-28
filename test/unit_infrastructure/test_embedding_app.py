"""
infrastructure.embedding.app FastAPI 앱 단위 테스트.
모델 로드는 mock.
"""
from __future__ import annotations

import unittest.mock

import pytest


@pytest.fixture
def client():
    mock_model = unittest.mock.Mock()
    try:
        import numpy as np
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    except ImportError:
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
    # 패치를 테스트 전체 동안 유지해야 /v1/embeddings 요청 시 503이 나지 않음
    with unittest.mock.patch("infrastructure.embedding.app._ensure_model", return_value=mock_model):
        from infrastructure.embedding.app import app
        from fastapi.testclient import TestClient
        yield TestClient(app)


class TestEmbeddingApp:
    """GET /health, POST /v1/embeddings 형식."""

    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data.get("status") == "ok"

    def test_embeddings_accepts_single_string(self, client):
        r = client.post(
            "/v1/embeddings",
            json={"model": "default", "input": "hello"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1
        assert "embedding" in data["data"][0]
        assert isinstance(data["data"][0]["embedding"], list)

    def test_embeddings_accepts_list_returns_multiple(self, client):
        r = client.post(
            "/v1/embeddings",
            json={"model": "default", "input": ["a", "b"]},
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert len(data["data"]) >= 1
