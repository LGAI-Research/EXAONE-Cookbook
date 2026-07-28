"""Tests for ToolAgent (rag): rag.retrieve tool."""
from __future__ import annotations

import unittest
import unittest.mock

from exaone.agents.rag_tools import RAG_TOOL_RETRIEVE, register_rag_tools
from exaone.agents.tool_agent_catalog import RAG_TOOL_AGENT_KEY, ToolAgentCatalog, qualify_tool_name
from exaone.retrieval.base_strategy import RetrievalResult
from exaone.tools import ToolRegistry


class TestRagTools(unittest.TestCase):
    def test_retrieve_returns_chunk_markers(self):
        strategy = unittest.mock.Mock()
        strategy.retrieve.return_value = [
            RetrievalResult(text="Fact A.", score=1.0),
            RetrievalResult(text="Fact B.", score=0.5),
        ]
        reg = ToolRegistry()
        register_rag_tools(reg, strategy)
        catalog = ToolAgentCatalog()
        catalog.register_tool_agent(RAG_TOOL_AGENT_KEY, reg)
        qname = qualify_tool_name(RAG_TOOL_AGENT_KEY, RAG_TOOL_RETRIEVE)
        out = catalog.dispatch(qname, {"query": "Q?", "top_k": 5})
        self.assertTrue(out.get("ok"))
        self.assertIn("<chunk index=", out.get("content", ""))
        strategy.retrieve.assert_called_once_with("Q?", top_k=5)
