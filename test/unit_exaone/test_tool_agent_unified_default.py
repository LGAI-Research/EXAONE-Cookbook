"""ToolAgent: plan_enrich_unified with answerable=false skips the enrich loop.

answerable=false 일 때 plan_enrich_unified 가 enrich 루프를 건너뛰는지 검증한다.
"""
from __future__ import annotations

import unittest
from unittest import mock


from exaone.agents.base_agent import AgentContext
from exaone.agents.prompts import ENRICH_PHASE_APPENDIX
from exaone.agents.tool_agent import ToolAgent
from exaone.llm import ExaoneResponse
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


class TestToolAgentUnifiedDefault(unittest.TestCase):
    def test_unified_not_answerable_skips_enrich_loop(self):
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
            max_enrich_turns=3,
        )
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
            answerable=False,
        )
        router.plan_finalize.return_value = mock.Mock(
            decision=route_decision,
            answer_tool_agent_key="answer",
            rewritten_query="q",
        )
        agent._get_thinking_router = lambda _llm: router

        with mock.patch.object(agent, "_run_reason_tool_loop") as mock_loop:
            agent.run(AgentContext(query="hello"), llm=llm)

        mock_loop.assert_not_called()
        router.plan_enrich_unified.assert_called_once()

    def test_not_answerable_setup_omits_enrich_appendix(self):
        llm = mock.Mock()
        llm.model = "test-model"

        agent = ToolAgent(
            tool_registry=_minimal_registry(),
            use_thinking_router=True,
            use_next_step_planner=False,
        )
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
            answerable=False,
        )
        agent._get_thinking_router = lambda _llm: router

        setup = agent._build_enrich_setup(AgentContext(query="hello"), llm, router=router)
        system_content = setup.messages[0].content
        self.assertNotIn(ENRICH_PHASE_APPENDIX.strip()[:40], system_content)

    def test_unified_not_answerable_skips_enrich_without_planner(self):
        llm = mock.Mock()
        llm.model = "test-model"
        llm.chat.return_value = ExaoneResponse(
            content='{"answer":"ok","confidence":"high"}',
            tool_calls=None,
        )

        agent = ToolAgent(
            tool_registry=_minimal_registry(),
            use_thinking_router=True,
            use_next_step_planner=False,
            max_enrich_turns=3,
        )
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
            answerable=False,
        )
        router.plan_finalize.return_value = mock.Mock(
            decision=route_decision,
            answer_tool_agent_key="answer",
            rewritten_query="q",
        )
        agent._get_thinking_router = lambda _llm: router

        with mock.patch.object(agent, "_run_reason_tool_loop") as mock_loop:
            agent.run(AgentContext(query="hello"), llm=llm)

        mock_loop.assert_not_called()
        router.plan_enrich_unified.assert_called_once()


if __name__ == "__main__":
    unittest.main()
