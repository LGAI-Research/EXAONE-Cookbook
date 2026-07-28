"""PR3: ToolAgent.run attaches llm_calls to result metadata."""
from __future__ import annotations

import unittest
from unittest import mock


from exaone.agents.base_agent import AgentContext
from exaone.agents.tool_agent import ToolAgent
from exaone.llm import ExaoneResponse
from exaone.observability import fields as obs_fields
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


class TestToolAgentLlmCallsMetadata(unittest.TestCase):
    def test_run_includes_llm_calls(self):
        llm = mock.Mock()
        llm.model = "test-model"
        llm.chat.side_effect = [
            ExaoneResponse(
                content=(
                    '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
                    '"semantic_intent":"general","confidence":"high","rationale":"ok",'
                    '"answerable":true,"tool_agent_key":"tool","rewritten_query":"hello",'
                    '"tool_hints":[]}'
                ),
                latency_ms=1.0,
            ),
            ExaoneResponse(
                content='{"answer_tool_agent_key":"answer","rewritten_query":"hello"}',
                latency_ms=2.0,
            ),
            ExaoneResponse(
                content='{"answer":"ok","confidence":"high"}',
                tool_calls=None,
                latency_ms=3.0,
            ),
        ]

        agent = ToolAgent(
            tool_registry=_registry(),
            use_thinking_router=True,
            use_next_step_planner=False,
            max_enrich_turns=1,
        )

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
            result = agent.run(AgentContext(query="hello"), llm=llm)

        self.assertIn(obs_fields.LLM_CALLS, result.metadata or {})
        phases = [c["phase"] for c in result.metadata[obs_fields.LLM_CALLS]]
        self.assertIn("route_plan_enrich_unified", phases)
        self.assertIn("route_plan_finalize", phases)
        self.assertIn("final_answer", phases)


if __name__ == "__main__":
    unittest.main()
