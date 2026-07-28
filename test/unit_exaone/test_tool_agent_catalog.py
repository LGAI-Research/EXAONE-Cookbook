"""ToolAgentCatalog: merge ToolAgent registries and qualified dispatch."""
from __future__ import annotations

import unittest

from exaone.agents.tool_agent_catalog import ToolAgentCatalog, qualify_tool_name
from exaone.tools import ToolRegistry, tool_from_callable


class TestToolAgentCatalog(unittest.TestCase):
    def test_qualified_schemas_and_dispatch(self):
        reg = ToolRegistry()

        def _echo(_n: str, args: dict) -> dict:
            return {"ok": True, "value": args.get("x")}

        reg.register(
            tool_from_callable(
                "echo",
                {
                    "type": "function",
                    "function": {
                        "name": "echo",
                        "description": "echo",
                        "parameters": {
                            "type": "object",
                            "properties": {"x": {"type": "string"}},
                        },
                    },
                },
                _echo,
            )
        )
        cat = ToolAgentCatalog.from_single_registry(reg, tool_agent_key="tool")
        schemas = cat.get_merged_schemas()
        self.assertEqual(schemas[0]["function"]["name"], "tool__echo")
        out = cat.dispatch("tool__echo", {"x": "hi"})
        self.assertEqual(out.get("value"), "hi")
        out_legacy = cat.dispatch("tool.echo", {"x": "legacy"})
        self.assertEqual(out_legacy.get("value"), "legacy")

    def test_unknown_qualified_tool_fails_cleanly(self):
        cat = ToolAgentCatalog.from_single_registry(ToolRegistry(), tool_agent_key="tool")
        out = cat.dispatch("tool__missing", {})
        self.assertIn("error", str(out).lower() or out)

    def test_catalog_entries_for_planner(self):
        reg = ToolRegistry()

        def _fn(_n: str, _a: dict) -> dict:
            return {}

        reg.register(
            tool_from_callable(
                "lookup",
                {
                    "type": "function",
                    "function": {
                        "name": "lookup",
                        "description": "Find facts",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
                _fn,
            )
        )
        cat = ToolAgentCatalog.from_single_registry(reg, tool_agent_key="rag")
        entries = cat.catalog_entries_for_planner()
        self.assertEqual(entries[0]["qualified_name"], "rag__lookup")
        self.assertEqual(entries[0]["description"], "Find facts")
