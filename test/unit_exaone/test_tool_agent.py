from __future__ import annotations

import unittest.mock

from exaone.agents.prompts import DEFAULT_SYSTEM_PROMPT_TOOL
from exaone.agents.tool_agent import ToolAgent
from exaone.llm import ExaoneResponse


class TestToolAgentSystemPrompt:
    def test_default_system_prompt_is_used_when_no_prompt_given(self):
        agent = ToolAgent()
        assert agent.system_prompt == DEFAULT_SYSTEM_PROMPT_TOOL

    def test_additional_system_prompt_is_appended_to_default(self):
        additional = "Always answer in JSON."
        agent = ToolAgent(additional_system_prompt=additional)

        assert agent.system_prompt.startswith(DEFAULT_SYSTEM_PROMPT_TOOL)
        assert additional in agent.system_prompt

    def test_additional_system_prompt_is_appended_to_custom_base(self):
        custom = "You are a strict internal assistant."
        additional = "Never reveal internal IDs."
        agent = ToolAgent(system_prompt=custom, additional_system_prompt=additional)

        assert agent.system_prompt.startswith(custom)
        assert additional in agent.system_prompt


class TestToolAgentThinkingRouter:
    def test_get_thinking_router_reuses_instance_for_same_llm(self):
        llm = unittest.mock.Mock()
        llm.model = "test-model"
        agent = ToolAgent()
        first = agent._get_thinking_router(llm)
        second = agent._get_thinking_router(llm)
        assert first is second

    def test_get_thinking_router_recreated_when_llm_changes(self):
        llm_a = unittest.mock.Mock()
        llm_a.model = "test-model"
        llm_b = unittest.mock.Mock()
        llm_b.model = "test-model"
        agent = ToolAgent()
        first = agent._get_thinking_router(llm_a)
        second = agent._get_thinking_router(llm_b)
        assert first is not second


class TestToolAgentFinalTurnRetry:
    def test_request_final_turn_json_returns_content(self):
        import unittest.mock

        mock_llm = unittest.mock.Mock(spec=["chat"])
        mock_llm.chat.return_value = ExaoneResponse(
            content='{"answer":"ok","confidence":"high"}',
            tool_calls=None,
        )
        content, reasoning = ToolAgent.request_final_turn(
            mock_llm,
            messages=[],
            max_new_tokens=256,
            verbose=False,
        )
        assert content == '{"answer":"ok","confidence":"high"}'
        assert reasoning is None
        mock_llm.chat.assert_called_once()
