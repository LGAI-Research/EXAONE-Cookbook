"""Tests for provider-agnostic LLM streaming normalization."""
from __future__ import annotations

import json
import unittest.mock

from exaone.llm.exaone_client import ExaoneAPIClient, ExaoneMessage
from exaone.llm.streaming import (
    LlmStreamChunk,
    iter_openai_compatible_sse,
    parse_openai_compatible_sse_line,
    stream_chunks_to_response,
)


def test_parse_text_delta():
    line = 'data: {"choices":[{"delta":{"content":"hi"}}]}'
    chunk = parse_openai_compatible_sse_line(line)
    assert chunk is not None
    assert chunk.kind == "text"
    assert chunk.text == "hi"


def test_parse_reasoning_delta():
    line = 'data: {"choices":[{"delta":{"reasoning_content":"think"}}]}'
    chunk = parse_openai_compatible_sse_line(line)
    assert chunk is not None
    assert chunk.kind == "reasoning"
    assert chunk.text == "think"


def test_parse_done():
    chunk = parse_openai_compatible_sse_line("data: [DONE]")
    assert chunk is not None
    assert chunk.kind == "done"


def test_stream_chunks_to_response_assembles_text():
    chunks = [
        LlmStreamChunk(kind="text", text="hel"),
        LlmStreamChunk(kind="text", text="lo"),
        LlmStreamChunk(kind="done", finish_reason="stop"),
    ]
    resp = stream_chunks_to_response(iter(chunks))
    assert resp.content == "hello"
    assert resp.finish_reason == "stop"


def test_iter_openai_compatible_sse_merges_tool_call_deltas():
    line1 = "data: " + json.dumps(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "c1",
                                "function": {"name": "calc", "arguments": '{"a":'},
                            }
                        ]
                    }
                }
            ]
        }
    )
    line2 = "data: " + json.dumps(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {"index": 0, "function": {"arguments": "1}"}},
                        ]
                    }
                }
            ]
        }
    )
    lines = [line1, line2, "data: [DONE]"]
    kinds = [c.kind for c in iter_openai_compatible_sse(iter(lines))]
    assert "tool_call" in kinds
    resp = stream_chunks_to_response(iter_openai_compatible_sse(iter(lines)))
    assert resp.tool_calls
    assert resp.tool_calls[0]["function"]["name"] == "calc"


def test_chat_stream_decodes_utf8_korean():
    korean = "남은 양은 9마리"
    payload = json.dumps(
        {"choices": [{"delta": {"content": korean}, "finish_reason": None}]},
        ensure_ascii=False,
    ).encode("utf-8")
    sse_lines = [b"data: " + payload, b"data: [DONE]"]

    mock_resp = unittest.mock.Mock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = iter(sse_lines)
    mock_resp.raise_for_status = unittest.mock.Mock()

    client = ExaoneAPIClient(base_url="http://test", api_key="k")
    with unittest.mock.patch("requests.post", return_value=mock_resp):
        chunks = list(
            client.chat_stream([ExaoneMessage(role="user", content="hi")])
        )

    text = "".join(c.text for c in chunks if c.kind == "text")
    assert text == korean
