"""Router tool hint prompt helpers."""
from __future__ import annotations

import unittest

from exaone.agents.thinking_router.hints import append_router_tool_hints
from exaone.agents.thinking_router.schemas import ROUTER_OUTPUT_FORMAT
from exaone.agents.thinking_router.types import (
    RouteDecision,
    RoutePlan,
    ToolCallHint,
)


def _route_plan(*, answerable: bool | None) -> RoutePlan:
    return RoutePlan(
        decision=RouteDecision(
            enable_thinking=True,
            temperature=1.0,
            top_p=0.95,
            final_response_format=ROUTER_OUTPUT_FORMAT,
            semantic_intent="structured",
        ),
        tool_agent_key="tool",
        rewritten_query="q",
        tool_hints=[
            ToolCallHint(
                name="tool__ping",
                arguments={"x": 1},
                reason="try",
            )
        ],
        answerable=answerable,
    )


class TestAppendRouterToolHints(unittest.TestCase):
    def test_skips_hints_when_not_answerable(self):
        out = append_router_tool_hints(
            "base",
            _route_plan(answerable=False),
            hints_header="Router enrich hints (soft; use when valid):",
        )
        self.assertEqual(out, "base")

    def test_appends_hints_when_answerable(self):
        out = append_router_tool_hints(
            "base",
            _route_plan(answerable=True),
            hints_header="Router enrich hints (soft; use when valid):",
        )
        self.assertIn("tool__ping", out)
        self.assertIn("Router enrich hints", out)

    def test_appends_hints_when_answerable_unknown(self):
        out = append_router_tool_hints(
            "base",
            _route_plan(answerable=None),
            hints_header="Router enrich hints (soft; use when valid):",
        )
        self.assertIn("tool__ping", out)


if __name__ == "__main__":
    unittest.main()
