"""PR1: skip screen_catalog LLM when ThinkingRouter enrich planning runs."""
from __future__ import annotations

import unittest
from unittest import mock


from exaone.agents.next_step_planner import CatalogScreenResult
from exaone.agents.tool_agent import ToolAgent
from exaone.agents.tool_agent_catalog import ToolAgentCatalog
from exaone.tools import ToolRegistry, tool_from_callable


def _minimal_registry() -> ToolRegistry:
    reg = ToolRegistry()

    def _noop(_n: str, _a: dict) -> dict:
        return {"ok": True}

    reg.register(
        tool_from_callable(
            "ping",
            {
                "type": "function",
                "function": {
                    "name": "ping",
                    "description": "ping",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            _noop,
        )
    )
    return reg


class TestToolAgentScreenSkip(unittest.TestCase):
    def test_should_run_screen_only_without_router(self):
        planner = mock.Mock()
        router = mock.Mock()
        self.assertTrue(ToolAgent._should_run_catalog_screen_llm(planner, None))
        self.assertFalse(ToolAgent._should_run_catalog_screen_llm(planner, router))
        self.assertFalse(ToolAgent._should_run_catalog_screen_llm(None, router))

    def test_run_skips_screen_when_router_and_planner_on(self):
        from exaone.agents.base_agent import AgentContext
        from exaone.llm import ExaoneResponse

        llm = mock.Mock()
        llm.model = "test-model"
        llm.chat.return_value = ExaoneResponse(
            content='{"answer":"ok","confidence":"high"}',
            tool_calls=None,
        )

        agent = ToolAgent(
            tool_registry=_minimal_registry(),
            use_thinking_router=True,
            use_next_step_planner=True,
            max_enrich_turns=1,
        )
        planner = mock.Mock()
        planner.screen_catalog = mock.Mock(
            return_value=CatalogScreenResult(
                answerable=False,
                tool_agent_key="tool",
                rationale="should not run",
            )
        )
        planner.evaluate_progress = mock.Mock()
        router = mock.Mock()
        route_decision = mock.Mock(
            enable_thinking=False,
            temperature=1.0,
            top_p=0.95,
            final_response_format=None,
        )
        router.plan_enrich_unified.return_value = mock.Mock(
            decision=route_decision,
            tool_agent_key="tool",
            rewritten_query="q",
            tool_hints=[],
        )
        router.plan_finalize.return_value = mock.Mock(
            decision=route_decision,
            answer_tool_agent_key="answer",
            rewritten_query="q",
        )

        agent._get_next_step_planner = mock.Mock(return_value=planner)  # type: ignore[method-assign]
        agent._get_thinking_router = mock.Mock(return_value=router)  # type: ignore[method-assign]

        with mock.patch.object(
            agent,
            "_run_reason_tool_loop",
            return_value=mock.Mock(
                messages=[],
                final_content="",
                error=None,
                turns_used=0,
                total_latency_ms=0.0,
            ),
        ):
            agent.run(AgentContext(query="hello"), llm=llm)

        planner.screen_catalog.assert_not_called()
        router.plan_enrich_unified.assert_called_once()

    def test_run_calls_screen_when_planner_only(self):
        from exaone.agents.base_agent import AgentContext
        from exaone.llm import ExaoneResponse

        llm = mock.Mock()
        llm.model = "test-model"
        llm.chat.return_value = ExaoneResponse(
            content='{"answer":"ok","confidence":"high"}',
            tool_calls=None,
        )

        agent = ToolAgent(
            tool_registry=_minimal_registry(),
            use_thinking_router=False,
            use_next_step_planner=True,
            max_enrich_turns=1,
        )
        planner = mock.Mock()
        planner.screen_catalog.return_value = CatalogScreenResult(
            answerable=True,
            tool_agent_key="tool",
            rationale="ok",
        )
        planner.evaluate_progress = mock.Mock()
        agent._get_next_step_planner = mock.Mock(return_value=planner)  # type: ignore[method-assign]

        with mock.patch.object(
            agent,
            "_run_reason_tool_loop",
            return_value=mock.Mock(
                messages=[],
                final_content="",
                error=None,
                turns_used=0,
                total_latency_ms=0.0,
            ),
        ):
            agent.run(AgentContext(query="hello"), llm=llm)

        planner.screen_catalog.assert_called_once()


if __name__ == "__main__":
    unittest.main()
