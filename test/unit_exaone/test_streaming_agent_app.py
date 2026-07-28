"""FastAPI SSE reference app smoke test."""
from __future__ import annotations

from fastapi.testclient import TestClient

from recipes.track02_minimum_agent_loop.streaming_demo.app import app


def test_health():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_agent_stream_sse_mock():
    client = TestClient(app)
    with client.stream("GET", "/v1/agent/stream", params={"query": "hi", "stream_llm": "false"}) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body = "".join(resp.iter_text())
    assert "event: run_start" in body
    assert "event: run_end" in body
