"""
(en) Unit tests for ``eval.runners.tau_bench_runner`` harness chat options.

(kr) ``eval.runners.tau_bench_runner`` harness chat options 단위 테스트.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from exaone.llm import ExaoneGenerateOptions, ExaoneMessage

from eval.runners.tau_bench_runner import _harness_complete


class _FakeLLM:
    def __init__(self) -> None:
        self.last_options: ExaoneGenerateOptions | None = None
        self.last_messages: list[Any] | None = None

    def chat(self, messages, options=None):
        self.last_messages = messages
        self.last_options = options
        return SimpleNamespace(
            content="hello",
            tool_calls=None,
            usage={"prompt_tokens": 3, "completion_tokens": 5},
        )


def test_harness_complete_uses_exaone_generate_options():
    llm = _FakeLLM()
    tools = [{"type": "function", "function": {"name": "lookup_order"}}]

    msg, (in_t, out_t) = _harness_complete(
        llm,
        messages=[{"role": "user", "content": "hi"}],
        tools=tools,
    )

    assert isinstance(llm.last_options, ExaoneGenerateOptions)
    assert llm.last_options.tools == tools
    assert llm.last_messages is not None
    assert len(llm.last_messages) == 1
    assert isinstance(llm.last_messages[0], ExaoneMessage)
    assert llm.last_messages[0].role == "user"
    assert msg["content"] == "hello"
    assert in_t == 3
    assert out_t == 5


def test_harness_complete_coerces_tool_messages():
    captured: list[Any] = []

    class _LLM:
        def chat(self, messages, options=None):
            captured.extend(messages)
            return SimpleNamespace(content="ok", tool_calls=None, usage={})

    _harness_complete(
        _LLM(),
        messages=[
            {"role": "system", "content": "wiki"},
            {"role": "user", "content": "hi"},
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "name": "lookup",
                "content": "result",
            },
        ],
        tools=[{"type": "function", "function": {"name": "lookup"}}],
    )

    assert len(captured) == 3
    assert all(isinstance(m, ExaoneMessage) for m in captured)
    assert captured[2].tool_call_id == "call_1"
    assert captured[2].name == "lookup"


def test_harness_complete_empty_tools_still_uses_exaone_generate_options():
    llm = _FakeLLM()

    _harness_complete(
        llm,
        messages=[{"role": "user", "content": "hi"}],
        tools=[],
    )

    assert isinstance(llm.last_options, ExaoneGenerateOptions)
    assert llm.last_options.tools is None
