"""Tests for agent semantic events during reason-tool loop."""
from __future__ import annotations

import unittest.mock

from exaone.agents.base_agent import BaseAgent
from exaone.agents.events import AgentEvent
from exaone.llm import ExaoneGenerateOptions, ExaoneMessage, ExaoneResponse
from exaone.llm.streaming import LlmStreamChunk


def test_iter_reason_tool_loop_emits_turn_and_tool_events():
    mock_llm = unittest.mock.Mock(spec=["chat"])
    mock_llm.chat.side_effect = [
        ExaoneResponse(
            content="",
            tool_calls=[
                {"id": "tc1", "function": {"name": "echo", "arguments": '{"x": 1}'}},
            ],
        ),
        ExaoneResponse(content='{"answer": "ok"}', tool_calls=None),
    ]
    msgs = [ExaoneMessage(role="user", content="hi")]

    with unittest.mock.patch(
        "exaone.agents.base_agent.ensure_input_within_limit",
        return_value=(msgs, None),
    ), unittest.mock.patch(
        "exaone.agents.base_agent.compress_messages_for_turn",
        side_effect=lambda m, _llm, **_kw: m,
    ):
        events = list(
            BaseAgent._iter_reason_tool_loop(
                mock_llm,
                msgs,
                tool_executor=lambda _n, _a: {"result": "pong"},
                options=ExaoneGenerateOptions(max_new_tokens=128, enable_thinking=False),
                max_turns=3,
            )
        )
    types = [e.type for e in events]
    assert types[0] == "run_start"
    assert "turn_start" in types
    assert "tool_start" in types
    assert "tool_end" in types
    assert types[-1] == "run_end"
    assert events[-1].payload.get("final_content") == '{"answer": "ok"}'


def test_run_reason_tool_loop_on_event_callback():
    mock_llm = unittest.mock.Mock(spec=["chat"])
    mock_llm.chat.return_value = ExaoneResponse(
        content='{"answer": "x", "confidence": "low"}',
        tool_calls=None,
    )
    msgs = [ExaoneMessage(role="user", content="hi")]
    collected: list[AgentEvent] = []
    with unittest.mock.patch(
        "exaone.agents.base_agent.ensure_input_within_limit",
        return_value=(msgs, None),
    ), unittest.mock.patch(
        "exaone.agents.base_agent.compress_messages_for_turn",
        side_effect=lambda m, _llm, **_kw: m,
    ):
        result = BaseAgent._run_reason_tool_loop(
            mock_llm,
            msgs,
            tool_executor=lambda _n, _a: {},
            options=ExaoneGenerateOptions(max_new_tokens=128, enable_thinking=False),
            max_turns=1,
            on_event=collected.append,
        )
    assert result.error is None
    assert any(e.type == "llm_end" for e in collected)
    assert collected[-1].type == "run_end"


def test_stream_llm_emits_llm_delta():
    mock_llm = unittest.mock.Mock()
    mock_llm.chat = unittest.mock.Mock()
    mock_llm.chat_stream.return_value = iter(
        [
            LlmStreamChunk(kind="text", text='{"answer":'),
            LlmStreamChunk(kind="text", text=' "done"}'),
            LlmStreamChunk(kind="done", finish_reason="stop"),
        ]
    )
    msgs = [ExaoneMessage(role="user", content="hi")]

    with unittest.mock.patch(
        "exaone.agents.base_agent.ensure_input_within_limit",
        return_value=(msgs, None),
    ), unittest.mock.patch(
        "exaone.agents.base_agent.compress_messages_for_turn",
        side_effect=lambda m, _llm, **_kw: m,
    ):
        events = list(
            BaseAgent._iter_reason_tool_loop(
                mock_llm,
                msgs,
                tool_executor=lambda _n, _a: {},
                options=ExaoneGenerateOptions(max_new_tokens=128, enable_thinking=False),
                max_turns=1,
                stream_llm=True,
            )
        )
    deltas = [e for e in events if e.type == "llm_delta"]
    assert len(deltas) == 2
    assert mock_llm.chat.call_count == 0
