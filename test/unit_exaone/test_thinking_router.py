"""Tests for ThinkingRouter: classifier + planner `response_format` injection."""

from __future__ import annotations

import unittest.mock

from exaone.agents.base_agent import ChatHistory
from exaone.agents.thinking_router import (
    CLASSIFY_RESPONSE_FORMAT,
    PLAN_RESPONSE_FORMAT,
    ROUTER_OUTPUT_FORMAT,
    RoutePlan,
    SemanticIntent,
    ThinkingRouter,
)
from exaone.llm import ExaoneGenerateOptions


def _axes_json(
    *,
    enable_thinking: bool = True,
    temperature: float = 1.0,
    top_p: float = 0.95,
    semantic_intent: str = "general",
    confidence: str = "high",
    rationale: str = "ok",
) -> str:
    import json

    return json.dumps(
        {
            "enable_thinking": enable_thinking,
            "temperature": temperature,
            "top_p": top_p,
            "semantic_intent": semantic_intent,
            "confidence": confidence,
            "rationale": rationale,
        },
        separators=(",", ":"),
    )


def _chat_response(content: str) -> unittest.mock.Mock:
    return unittest.mock.Mock(content=content)


class TestThinkingRouterResponseFormat(unittest.TestCase):
    def test_router_output_format_unified_agent_schema(self):
        schema = ROUTER_OUTPUT_FORMAT["json_schema"]["schema"]
        self.assertEqual(schema["required"], ["answer", "confidence"])
        props = schema["properties"]
        self.assertIn("sources", props)
        self.assertNotIn("semantic_intent", props)
        self.assertNotIn("tool_instruction", props)

    def test_route_passes_classify_response_format(self):
        mock_client = unittest.mock.Mock()
        mock_client.chat.return_value = _chat_response(
            _axes_json(semantic_intent="analytical", enable_thinking=True)
        )
        router = ThinkingRouter(mock_client, "dummy-model")
        decision = router.route("compare A and B", has_context=True)
        self.assertEqual(decision.semantic_intent, SemanticIntent.ANALYTICAL.value)
        self.assertTrue(decision.enable_thinking)
        mock_client.chat.assert_called_once()
        opts = mock_client.chat.call_args.kwargs.get("options")
        self.assertIsInstance(opts, ExaoneGenerateOptions)
        self.assertEqual(opts.response_format, CLASSIFY_RESPONSE_FORMAT)
        self.assertFalse(opts.enable_thinking)

    def test_plan_injects_both_classify_and_plan_response_format(self):
        mock_client = unittest.mock.Mock()
        mock_client.chat.side_effect = [
            _chat_response(
                _axes_json(semantic_intent="structured", enable_thinking=False, temperature=0.3)
            ),
            _chat_response(
                '{"tool_agent_key":"tool","rewritten_query":"Seoul weather",'
                '"tool_hints":[{"name":"tool__weather_lookup","arguments":{"city":"Seoul"},'
                '"reason":"live weather"}]}'
            ),
        ]
        router = ThinkingRouter(mock_client, "dummy-model")
        plan = router.plan_enrich(
            "서울 날씨 알려줘",
            has_tools=True,
            available_tools=["tool__weather_lookup"],
            default_tool_agent_key="tool",
        )
        self.assertEqual(plan.tool_agent_key, "tool")
        self.assertEqual(plan.agent_key, "tool")
        self.assertEqual(plan.phase, "enrich")
        self.assertTrue(plan.tool_hints)
        self.assertEqual(plan.tool_hints[0].name, "tool__weather_lookup")
        self.assertEqual(plan.tool_hints[0].arguments.get("city"), "Seoul")
        self.assertEqual(mock_client.chat.call_count, 2)
        classify_opts = mock_client.chat.call_args_list[0].kwargs.get("options")
        plan_opts = mock_client.chat.call_args_list[1].kwargs.get("options")
        self.assertEqual(classify_opts.response_format, CLASSIFY_RESPONSE_FORMAT)
        self.assertEqual(plan_opts.response_format, PLAN_RESPONSE_FORMAT)
        self.assertIsInstance(plan, RoutePlan)
        self.assertTrue(hasattr(plan, "decision"))
        self.assertFalse(hasattr(plan, "profile"))
        self.assertEqual(plan.decision.semantic_intent, SemanticIntent.STRUCTURED.value)

    def test_route_uses_in_memory_cache(self):
        mock_client = unittest.mock.Mock()
        mock_client.chat.return_value = _chat_response(
            _axes_json(semantic_intent="general", enable_thinking=False)
        )
        router = ThinkingRouter(mock_client, "dummy-model")
        d1 = router.route("cached query")
        d2 = router.route("cached query")
        self.assertIs(d1, d2)
        mock_client.chat.assert_called_once()

    def test_exaone_agents_exports_router_types(self):
        from exaone.agents import RouteDecision, SemanticIntent, ThinkingRouter

        self.assertTrue(callable(ThinkingRouter))
        self.assertTrue(hasattr(RouteDecision, "__dataclass_fields__"))
        self.assertTrue(any(m.value == "analytical" for m in SemanticIntent))

    def test_normalize_history_chat_history_turns(self):
        from exaone.agents.base_agent import BaseAgent

        turns = BaseAgent.normalize_chat_history_turns(
            [ChatHistory(role="user", content="이전 질문")]
        )
        self.assertEqual(turns, [{"role": "user", "content": "이전 질문"}])

    def test_normalize_history_mixed_dict_and_chat_history(self):
        from exaone.agents.base_agent import BaseAgent

        turns = BaseAgent.normalize_chat_history_turns(
            [
                {"role": "user", "content": "dict turn"},
                ChatHistory(role="assistant", content="typed turn"),
            ]
        )
        self.assertEqual(
            turns,
            [
                {"role": "user", "content": "dict turn"},
                {"role": "assistant", "content": "typed turn"},
            ],
        )

    def test_route_accepts_chat_history_without_error(self):
        mock_client = unittest.mock.Mock()
        mock_client.chat.return_value = _chat_response(
            _axes_json(semantic_intent="general", enable_thinking=False)
        )
        router = ThinkingRouter(mock_client, "dummy-model")
        decision = router.route(
            "follow-up",
            history=[ChatHistory(role="user", content="첫 질문")],
        )
        self.assertEqual(decision.semantic_intent, SemanticIntent.GENERAL.value)
        mock_client.chat.assert_called_once()
        user_msg = mock_client.chat.call_args[0][0][-1]
        self.assertIn("첫 질문", user_msg.content)

    def test_route_cache_key_differs_by_chat_history(self):
        from exaone.agents.thinking_router import RouteContext

        ctx_a = RouteContext(history=[{"role": "user", "content": "A"}])
        from exaone.agents.base_agent import BaseAgent

        ctx_b = RouteContext(
            history=BaseAgent.normalize_chat_history_turns(
                [ChatHistory(role="user", content="B")]
            )
        )
        key_a = ThinkingRouter._route_cache_key("q", ctx_a)
        key_b = ThinkingRouter._route_cache_key("q", ctx_b)
        self.assertNotEqual(key_a, key_b)
