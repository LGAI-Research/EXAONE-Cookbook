"""Tests for LLM response quality helpers and empty-content recovery."""
from __future__ import annotations

import unittest.mock

from exaone.llm.exaone_client import (
    ExaoneAPIClient,
    ExaoneGenerateOptions,
    ExaoneMessage,
    ExaoneResponse,
)
from exaone.llm.response_quality import (
    is_empty_llm_response,
    is_reasoning_only_llm_response,
    needs_content_recovery,
)
from exaone.llm.streaming import LlmStreamChunk, stream_chunks_to_response


def test_is_empty_without_content_reasoning_or_tools():
    resp = ExaoneResponse(content="", reasoning_content=None, tool_calls=None)
    assert is_empty_llm_response(resp)
    assert needs_content_recovery(resp)


def test_is_reasoning_only():
    resp = ExaoneResponse(
        content="",
        reasoning_content="internal chain of thought",
        tool_calls=None,
    )
    assert is_reasoning_only_llm_response(resp)
    assert needs_content_recovery(resp)


def test_tool_calls_are_not_empty():
    resp = ExaoneResponse(
        content="",
        reasoning_content="think",
        tool_calls=[{"id": "1", "function": {"name": "x", "arguments": "{}"}}],
    )
    assert not is_empty_llm_response(resp)
    assert not is_reasoning_only_llm_response(resp)


def test_stream_chunks_keeps_reasoning_separate():
    chunks = [
        LlmStreamChunk(kind="reasoning", text="thinking only"),
        LlmStreamChunk(kind="done", finish_reason="stop"),
    ]
    resp = stream_chunks_to_response(iter(chunks))
    assert resp.content == ""
    assert resp.reasoning_content == "thinking only"


class TestExaoneClientEmptyRecovery(unittest.TestCase):
    def test_chat_retries_with_thinking_off(self):
        client = ExaoneAPIClient(base_url="http://test", api_key="k")
        reasoning_only = {
            "choices": [
                {
                    "message": {"content": "", "reasoning_content": "thought"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {},
        }
        fixed = {
            "choices": [
                {
                    "message": {
                        "content": '{"answer":"ok","confidence":"high","sources":[]}',
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {},
        }

        mock_resp = unittest.mock.Mock()
        mock_resp.status_code = 200
        mock_resp.text = "{}"

        with unittest.mock.patch.object(client, "_parse_response_with_output_pipeline") as parse:
            with unittest.mock.patch("requests.post", return_value=mock_resp) as post:
                parse.side_effect = [reasoning_only, fixed]
                out = client.chat(
                    [ExaoneMessage(role="user", content="hi")],
                    options=ExaoneGenerateOptions(
                        max_new_tokens=100,
                        enable_thinking=True,
                    ),
                )
        self.assertEqual(post.call_count, 2)
        self.assertIn("ok", out.content)
        self.assertIsNone(out.reasoning_content)
