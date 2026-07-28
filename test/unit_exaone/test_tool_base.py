from __future__ import annotations

from dataclasses import dataclass

from exaone.tools.base import Tool, tool_from_typed_callable


@dataclass
class AddInput:
    a: int
    b: int


class TestToolStructuredInput:
    def test_tool_run_supports_input_model(self):
        tool = Tool(
            name="add",
            schema={"type": "function", "function": {"name": "add"}},
            input_model=AddInput,
            execute=lambda args: {"result": args.a + args.b},
        )

        out = tool.run({"a": 2, "b": 3})
        assert out["result"] == 5

    def test_tool_run_supports_custom_input_parser(self):
        tool = Tool(
            name="add",
            schema={"type": "function", "function": {"name": "add"}},
            input_parser=lambda d: AddInput(a=int(d["x"]), b=int(d["y"])),
            execute=lambda args: {"result": args.a + args.b},
        )

        out = tool.run({"x": "4", "y": "5"})
        assert out["result"] == 9

    def test_tool_from_typed_callable(self):
        def _run(_name: str, args: AddInput):
            return {"sum": args.a + args.b}

        tool = tool_from_typed_callable(
            name="sum",
            schema={"type": "function", "function": {"name": "sum"}},
            input_model=AddInput,
            fn=_run,
        )

        out = tool.run({"a": 7, "b": 8})
        assert out["sum"] == 15
