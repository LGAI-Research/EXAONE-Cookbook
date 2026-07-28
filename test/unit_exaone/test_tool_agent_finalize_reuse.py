"""PR2: ToolAgent passes enrich RouteDecision into plan_finalize."""
from __future__ import annotations

import unittest
from unittest import mock


from exaone.agents.base_agent import AgentContext
from exaone.agents.thinking_router.schemas import ROUTER_OUTPUT_FORMAT
from exaone.agents.thinking_router.types import RouteDecision
from exaone.agents.tool_agent import ToolAgent
from exaone.llm import ExaoneResponse
from exaone.tools import ToolRegistry, tool_from_callable


def _registry() -> ToolRegistry:
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


class TestToolAgentFinalizeReuse(unittest.TestCase):
    def test_finalize_passes_enrich_decision(self):
        llm = mock.Mock()
        llm.model = "test-model"
        llm.chat.return_value = ExaoneResponse(
            content='{"answer":"ok","confidence":"high"}',
            tool_calls=None,
        )

        enrich_decision = RouteDecision(
            enable_thinking=True,
            temperature=0.7,
            top_p=0.95,
            final_response_format=ROUTER_OUTPUT_FORMAT,
            semantic_intent="general",
        )
        route_plan = mock.Mock(
            decision=enrich_decision,
            tool_agent_key="tool",
            rewritten_query="hello",
            tool_hints=[],
        )

        agent = ToolAgent(
            tool_registry=_registry(),
            use_thinking_router=True,
            use_next_step_planner=False,
            max_enrich_turns=1,
        )
        router = mock.Mock()
        router.plan_enrich_unified.return_value = route_plan
        router.plan_finalize.return_value = mock.Mock(
            decision=enrich_decision,
            answer_tool_agent_key="answer",
            rewritten_query="hello",
        )
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

        router.plan_finalize.assert_called_once()
        _kwargs = router.plan_finalize.call_args.kwargs
        self.assertIs(_kwargs.get("enrich_decision"), enrich_decision)


if __name__ == "__main__":
    unittest.main()
