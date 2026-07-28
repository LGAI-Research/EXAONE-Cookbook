from __future__ import annotations

import pytest

from eval.datasets.schema import EvalTask, ExpectedToolCall, ToolSpec
from eval.runners.common import (
    ABSTENTION_APPENDIX,
    DEFAULT_SYSTEM_PROMPT,
    TOOL_TRAJECTORY_APPENDIX,
    CapturedExecutor,
    harness_agent_options,
    is_abstention_task,
    is_tool_trajectory_task,
    normalize_tool_call_args,
    system_prompt_for,
    to_function_schema,
    tools_to_schemas,
)


class TestToFunctionSchema:
    def test_wraps_tool_spec(self):
        spec = ToolSpec(name="f", description="d", parameters={"type": "object"})
        out = to_function_schema(spec)
        assert out["type"] == "function"
        assert out["function"]["name"] == "f"
        assert out["function"]["parameters"]["type"] == "object"

    def test_defaults_empty_parameters(self):
        spec = ToolSpec(name="f", description="", parameters={})
        out = to_function_schema(spec)
        assert out["function"]["parameters"] == {"type": "object", "properties": {}}


class TestCapturedExecutor:
    def test_records_calls_in_order(self):
        ex = CapturedExecutor(task_id="t")
        ex("a", {"x": 1})
        ex("b", {"y": 2})
        assert [c.name for c in ex.calls] == ["a", "b"]
        assert ex.calls[0].arguments == {"x": 1}

    def test_returns_stub_payload(self):
        ex = CapturedExecutor()
        result = ex("a", {"x": 1})
        assert result["ok"] is True
        assert result["echo"] == {"x": 1}

    def test_coerces_non_dict_args_to_empty(self):
        ex = CapturedExecutor()
        # (en) Deliberately pass None to exercise non-dict argument coercion.
        # (kr) None 을 넘겨 non-dict 인자 강제 변환 경로를 검증한다.
        bad_args: object = None
        ex("a", bad_args)
        assert ex.calls[0].arguments == {}


class TestNormalizeToolCallArgs:
    def test_parses_json_string(self):
        assert normalize_tool_call_args('{"a": 1}') == {"a": 1}

    def test_passes_through_dict(self):
        assert normalize_tool_call_args({"a": 1}) == {"a": 1}

    def test_empty_string(self):
        assert normalize_tool_call_args("") == {}

    def test_invalid_json_returns_empty(self):
        assert normalize_tool_call_args("not json") == {}

    def test_none(self):
        assert normalize_tool_call_args(None) == {}


class TestBuildCapturingRegistry:
    def test_registers_tools_and_captures_executions(self):
        from eval.runners.common import build_capturing_registry

        tools = [ToolSpec(name="get_weather", description="", parameters={"type": "object"})]
        registry, executor = build_capturing_registry(tools, task_id="t")
        assert registry.get("get_weather") is not None
        registry.execute("get_weather", {"city": "Seoul"})
        assert len(executor.calls) == 1
        assert executor.calls[0].name == "get_weather"
        assert executor.calls[0].arguments == {"city": "Seoul"}

    def test_unknown_tool_returns_failure_payload_not_exception(self):
        from eval.runners.common import build_capturing_registry

        registry, executor = build_capturing_registry([])
        out = registry.execute("missing", {})
        assert out.get("error")
        assert len(executor.calls) == 0


class TestSystemPromptFor:
    def test_default_base_only_for_plain_task(self):
        task = EvalTask(
            task_id="plain-1",
            dataset="custom",
            category="x",
            query="hello",
        )
        assert system_prompt_for(task) == DEFAULT_SYSTEM_PROMPT

    def test_tool_trajectory_appendix_from_expected_calls(self):
        task = EvalTask(
            task_id="tool-1",
            dataset="custom",
            category="x",
            query="call api",
            expected_tool_calls=[ExpectedToolCall(name="search", arguments={"q": "x"})],
        )
        prompt = system_prompt_for(task)
        assert prompt.startswith(DEFAULT_SYSTEM_PROMPT)
        assert TOOL_TRAJECTORY_APPENDIX in prompt
        assert "parallel tool_calls" in TOOL_TRAJECTORY_APPENDIX
        assert "every relevant catalog call" in TOOL_TRAJECTORY_APPENDIX
        assert "scalar arguments per pair" in TOOL_TRAJECTORY_APPENDIX
        assert "every matching tool call" in DEFAULT_SYSTEM_PROMPT
        assert ABSTENTION_APPENDIX not in prompt

    def test_tool_trajectory_appendix_from_bfcl_metadata(self):
        task = EvalTask(
            task_id="tool-2",
            dataset="custom",
            category="x",
            query="call api",
            metadata={"bfcl_ground_truth": [{"search": {"q": ["x"]}}]},
        )
        assert is_tool_trajectory_task(task)
        assert TOOL_TRAJECTORY_APPENDIX in system_prompt_for(task)

    def test_abstention_appendix_when_expected_no_tools(self):
        task = EvalTask(
            task_id="irr-1",
            dataset="custom",
            category="x",
            query="chitchat",
            expected_no_tools=True,
        )
        prompt = system_prompt_for(task)
        assert prompt.startswith(DEFAULT_SYSTEM_PROMPT)
        assert ABSTENTION_APPENDIX in prompt
        assert is_abstention_task(task)

    def test_custom_task_system_prompt_unchanged(self):
        custom = "You are a domain-specific assistant."
        task = EvalTask(
            task_id="tau-1",
            dataset="tau_bench",
            category="retail",
            query="hi",
            system_prompt=custom,
            expected_tool_calls=[ExpectedToolCall(name="a", arguments={})],
        )
        assert system_prompt_for(task) == custom


class TestHarnessAgentOptions:
    def test_disables_router_planner_for_tool_trajectory_scope(self):
        task = EvalTask(
            task_id="tool-1",
            dataset="custom",
            category="x",
            query="call api",
            metadata={"bfcl_ground_truth": [{"search": {"q": ["x"]}}]},
        )
        opts = harness_agent_options(task)
        assert opts == {"use_thinking_router": False, "use_next_step_planner": False}

    def test_enables_planner_only_for_abstention_scope(self):
        task = EvalTask(
            task_id="irr-1",
            dataset="custom",
            category="x",
            query="chitchat",
            expected_no_tools=True,
        )
        opts = harness_agent_options(task)
        assert opts == {"use_thinking_router": False, "use_next_step_planner": True}

    def test_keeps_router_planner_for_plain_eval_task(self):
        task = EvalTask(
            task_id="plain-1",
            dataset="custom",
            category="x",
            query="hello",
        )
        opts = harness_agent_options(task)
        assert opts == {"use_thinking_router": True, "use_next_step_planner": True}

    def test_custom_system_prompt_keeps_router_planner(self):
        task = EvalTask(
            task_id="tau-1",
            dataset="tau_bench",
            category="retail",
            query="hi",
            system_prompt="wiki",
            expected_no_tools=True,
        )
        opts = harness_agent_options(task)
        assert opts == {"use_thinking_router": True, "use_next_step_planner": True}
