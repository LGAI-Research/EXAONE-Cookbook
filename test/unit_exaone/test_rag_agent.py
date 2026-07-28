"""ToolAgent + ThinkingRouter (replaces RAGAgent-specific tests)."""
from __future__ import annotations

import unittest
import unittest.mock

from exaone.agents.tool_agent import ToolAgent
from exaone.agents.rag_tools import build_rag_tool_registry


class TestToolAgentThinkingRouter(unittest.TestCase):
    def test_get_thinking_router_reuses_instance_for_same_llm(self):
        llm = unittest.mock.Mock()
        llm.model = "test-model"
        agent = ToolAgent()
        first = agent._get_thinking_router(llm)
        second = agent._get_thinking_router(llm)
        self.assertIs(first, second)

    def test_get_thinking_router_recreated_when_llm_changes(self):
        llm_a = unittest.mock.Mock()
        llm_a.model = "model-a"
        llm_b = unittest.mock.Mock()
        llm_b.model = "model-b"
        agent = ToolAgent()
        first = agent._get_thinking_router(llm_a)
        second = agent._get_thinking_router(llm_b)
        self.assertIsNot(first, second)

    def test_rag_tool_agent_registered_when_retrieval_strategy_set(self):
        strategy = unittest.mock.Mock()
        agent = ToolAgent(retrieval_strategy=strategy)
        self.assertIn("rag", agent.catalog.tool_agent_keys)
        names = agent.catalog.catalog_tool_names()
        self.assertTrue(any(n.startswith("rag__") for n in names))
