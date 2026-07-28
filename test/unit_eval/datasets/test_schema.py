"""
(en) Schema round-trip tests for `eval/datasets/schema.py`. Pure in-memory,
no network — runs offline.

(kr) `eval/datasets/schema.py`의 round-trip 테스트이다. 메모리 전용이며 네트워크 의존이 없다.
"""
from __future__ import annotations

from eval.datasets.schema import EvalTask, ExpectedToolCall, ToolSpec


def test_eval_task_to_dict_minimal():
    t = EvalTask(
        task_id="t1",
        dataset="bfcl_v3.simple",
        category="simple",
        query="hello",
    )
    d = t.to_dict()
    assert d["task_id"] == "t1"
    assert d["dataset"] == "bfcl_v3.simple"
    assert d["tools"] == []
    assert d["expected_tool_calls"] is None
    assert d["expected_no_tools"] is False
    assert d["metadata"] == {}


def test_eval_task_round_trip_with_tools_and_calls():
    original = EvalTask(
        task_id="t2",
        dataset="bfcl_v3.simple",
        category="simple",
        query="add 2 and 3",
        tools=[
            ToolSpec(
                name="math.add",
                description="add two numbers",
                parameters={"type": "object", "properties": {"a": {"type": "integer"}}},
            )
        ],
        expected_tool_calls=[ExpectedToolCall(name="math.add", arguments={"a": 2, "b": 3})],
        metadata={"src": "unit"},
    )

    payload = original.to_dict()
    restored = EvalTask.from_dict(payload)

    assert restored.task_id == original.task_id
    assert restored.dataset == original.dataset
    assert restored.tools[0].name == "math.add"
    assert isinstance(restored.tools[0], ToolSpec)
    assert restored.expected_tool_calls is not None
    assert isinstance(restored.expected_tool_calls[0], ExpectedToolCall)
    assert restored.expected_tool_calls[0].arguments == {"a": 2, "b": 3}
    assert restored.metadata == {"src": "unit"}


def test_eval_task_from_dict_ignores_unknown_keys():
    payload = {
        "task_id": "t3",
        "dataset": "ifeval",
        "category": "verifiable_instructions",
        "query": "write something",
        "future_field": "ignored",
    }
    restored = EvalTask.from_dict(payload)
    assert restored.task_id == "t3"
    assert restored.dataset == "ifeval"


def test_eval_task_irrelevance_shape():
    t = EvalTask(
        task_id="irr_0",
        dataset="bfcl_v3.irrelevance",
        category="irrelevance",
        query="random",
        tools=[ToolSpec(name="x", description="d", parameters={"type": "object"})],
        expected_tool_calls=None,
        expected_no_tools=True,
    )
    d = t.to_dict()
    assert d["expected_no_tools"] is True
    assert d["expected_tool_calls"] is None
