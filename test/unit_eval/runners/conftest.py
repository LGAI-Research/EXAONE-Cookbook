"""
(en) Shared fixtures: synthetic EvalTask instances + fake LLM / chat callable that
let both runner test suites run fully offline.

(kr) 공통 fixture. 합성 EvalTask + fake LLM / chat callable로 두 runner 테스트가
오프라인에서 완전히 동작하도록 한다.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from eval.datasets.schema import EvalTask, ExpectedToolCall, ToolSpec


@pytest.fixture()
def bfcl_like_task() -> EvalTask:
    return EvalTask(
        task_id="bfcl.simple.001",
        dataset="bfcl_v3.simple",
        category="simple",
        query="What is the weather in Seoul?",
        tools=[
            ToolSpec(
                name="get_weather",
                description="Return current weather for a city.",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            )
        ],
        expected_tool_calls=[
            ExpectedToolCall(name="get_weather", arguments={"city": "Seoul"})
        ],
    )


@pytest.fixture()
def irrelevance_task() -> EvalTask:
    return EvalTask(
        task_id="bfcl.irr.002",
        dataset="bfcl_v3.irrelevance",
        category="irrelevance",
        query="What time is it on Mars?",
        tools=[
            ToolSpec(
                name="get_weather",
                description="Return current weather for a city.",
                parameters={"type": "object", "properties": {"city": {"type": "string"}}},
            )
        ],
        expected_tool_calls=None,
        expected_no_tools=True,
    )


@pytest.fixture()
def ifeval_like_task() -> EvalTask:
    return EvalTask(
        task_id="ifeval.001",
        dataset="ifeval",
        category="length_constraints",
        query="Write a haiku about a database.",
        tools=[],
    )


def _make_chat_response(
    *,
    content: str = "",
    tool_calls: list[dict[str, Any]] | None = None,
    prompt_tokens: int = 50,
    completion_tokens: int = 30,
    finish_reason: str = "stop",
) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return {
        "choices": [{"message": msg, "finish_reason": finish_reason}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


@pytest.fixture()
def make_chat_response():
    return _make_chat_response


@pytest.fixture()
def chat_fn_scripted():
    """
    (en) Returns a factory that builds a deterministic ``chat_fn`` from a list of
    canned response dicts (each call pops the next one).

    (kr) 정해진 응답 dict 리스트로 결정론적 ``chat_fn``을 만드는 factory를 반환한다.
    """

    def _factory(responses: list[dict[str, Any]]):
        state = {"i": 0, "calls": []}

        def _chat(*, messages, tools):
            i = state["i"]
            if i >= len(responses):
                raise AssertionError(f"chat_fn called {i + 1} times but only {len(responses)} responses queued")
            state["i"] += 1
            state["calls"].append({"messages": messages, "tools": tools})
            return responses[i]

        _chat.state = state
        return _chat

    return _factory


class _FakeExaoneClient:
    """
    (en) Drop-in stand-in for `ExaoneAPIClient` used in tests. Returns canned
    `ExaoneResponse` instances in order. Does NOT inherit from `ExaoneClient` so
    we can avoid pulling the abstract base when ToolAgent only type-checks at runtime.

    (kr) 테스트용 `ExaoneAPIClient` 대체. 정해진 `ExaoneResponse`를 순서대로 반환.
    `ExaoneClient` 상속은 하지 않음(ToolAgent는 런타임에서만 타입을 본다).
    """

    DEFAULT_MODEL = "test-model"

    def __init__(self, responses):
        self._responses = list(responses)
        self._i = 0
        self.model = "test-model"

    def chat(self, messages, options=None):
        if self._i >= len(self._responses):
            raise AssertionError(
                f"FakeExaoneClient.chat called {self._i + 1} times but only "
                f"{len(self._responses)} responses queued"
            )
        resp = self._responses[self._i]
        self._i += 1
        return resp


@pytest.fixture()
def fake_exaone_client():
    return _FakeExaoneClient


@pytest.fixture()
def make_assistant_tool_call():
    """
    (en) Build one OpenAI-style ``tool_calls`` entry — arguments must be a JSON string.

    (kr) OpenAI 스타일 ``tool_calls`` 항목 하나를 만든다. arguments는 JSON 문자열.
    """

    def _factory(name: str, arguments: dict[str, Any], *, call_id: str = "call_1"):
        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(arguments, ensure_ascii=False),
            },
        }

    return _factory
