from __future__ import annotations

import pytest


from exaone.tools.base import Tool
from exaone.tools.results import is_tool_failure_payload
from exaone.tools.tool_registry import ToolRegistry


def _ok_execute(arguments: dict):
    return {"ok": True, "arguments": arguments}


class TestToolRegistrySchemaValidation:
    def test_register_raises_when_schema_type_is_missing(self):
        reg = ToolRegistry()
        tool = Tool(
            name="bad_tool",
            schema={"function": {"name": "bad_tool"}},
            execute=_ok_execute,
        )

        with pytest.raises(ValueError, match="type='function'"):
            reg.register(tool)

    def test_register_raises_when_schema_type_is_not_function(self):
        reg = ToolRegistry()
        tool = Tool(
            name="bad_tool",
            schema={"type": "object", "function": {"name": "bad_tool"}},
            execute=_ok_execute,
        )

        with pytest.raises(ValueError, match="type='function'"):
            reg.register(tool)

    def test_register_raises_when_function_name_is_missing(self):
        reg = ToolRegistry()
        tool = Tool(
            name="bad_tool",
            schema={"type": "function", "function": {"description": "x"}},
            execute=_ok_execute,
        )

        with pytest.raises(ValueError, match="must have 'name'"):
            reg.register(tool)

    def test_register_accepts_valid_schema(self):
        reg = ToolRegistry()
        tool = Tool(
            name="ok_tool",
            schema={"type": "function", "function": {"name": "ok_tool", "parameters": {"type": "object"}}},
            execute=_ok_execute,
        )

        reg.register(tool)

        assert reg.get("ok_tool") is not None
        assert len(reg) == 1

    def test_register_raises_when_tool_name_differs_from_schema_name(self):
        reg = ToolRegistry()
        tool = Tool(
            name="tool_a",
            schema={"type": "function", "function": {"name": "tool_b"}},
            execute=_ok_execute,
        )

        with pytest.raises(ValueError, match="does not match schema function.name"):
            reg.register(tool)

    def test_register_raises_when_name_already_registered(self):
        reg = ToolRegistry()
        schema = {"type": "function", "function": {"name": "dup_tool"}}
        reg.register(Tool(name="dup_tool", schema=schema, execute=_ok_execute))

        with pytest.raises(ValueError, match="Tool already registered: dup_tool"):
            reg.register(Tool(name="dup_tool", schema=schema, execute=_ok_execute))


class TestToolRegistryExecuteValidation:
    def test_execute_returns_error_when_tool_unknown(self):
        reg = ToolRegistry()
        out = reg.execute("missing", {"x": 1})
        assert "Unknown tool" in out["error"]
        assert is_tool_failure_payload(out)

    def test_execute_returns_error_when_arguments_invalid(self):
        reg = ToolRegistry()
        tool = Tool(
            name="sum_tool",
            schema={
                "type": "function",
                "function": {
                    "name": "sum_tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"a": {"type": "number"}},
                        "required": ["a"],
                    },
                },
            },
            execute=_ok_execute,
        )
        reg.register(tool)

        out = reg.execute("sum_tool", {"a": "not-number"})
        assert "Invalid arguments:" in out["error"]
        assert is_tool_failure_payload(out)

    def test_execute_runs_tool_when_arguments_valid(self):
        reg = ToolRegistry()
        tool = Tool(
            name="sum_tool",
            schema={
                "type": "function",
                "function": {
                    "name": "sum_tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"a": {"type": "number"}},
                        "required": ["a"],
                    },
                },
            },
            execute=_ok_execute,
        )
        reg.register(tool)

        out = reg.execute("sum_tool", {"a": 1})
        assert out["ok"] is True

    def test_execute_skips_validation_when_parameters_schema_missing(self):
        reg = ToolRegistry()
        tool = Tool(
            name="loose_tool",
            schema={"type": "function", "function": {"name": "loose_tool"}},
            execute=_ok_execute,
        )
        reg.register(tool)

        out = reg.execute("loose_tool", {"anything": "goes"})
        assert out["ok"] is True
