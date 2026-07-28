"""Thinking router: unified plan_enrich (single LLM) with legacy fallback.

단일 LLM plan_enrich 통합 경로와 레거시 폴백을 검증한다.
"""
from __future__ import annotations

import json
import unittest
from unittest import mock


from exaone.agents.thinking_router.router import ThinkingRouter
from exaone.agents.thinking_router.schemas import (
    CLASSIFY_RESPONSE_FORMAT,
    PLAN_RESPONSE_FORMAT,
    UNIFIED_PLAN_RESPONSE_FORMAT,
)


def _unified_json(*, answerable: bool = True) -> str:
    return json.dumps(
        {
            "enable_thinking": True,
            "temperature": 1.0,
            "top_p": 0.95,
            "semantic_intent": "structured",
            "confidence": "high",
            "rationale": "ok",
            "answerable": answerable,
            "tool_agent_key": "tool",
            "rewritten_query": "q rewritten",
            "tool_hints": [],
        },
        separators=(",", ":"),
    )


class TestPlanEnrichUnified(unittest.TestCase):
    def test_unified_single_llm_call(self):
        mock_client = mock.Mock()
        mock_client.chat.return_value = mock.Mock(content=_unified_json())
        router = ThinkingRouter(mock_client, "m")
        plan = router.plan_enrich_unified(
            "hello",
            has_tools=True,
            available_tools=["tool__ping"],
            default_tool_agent_key="tool",
        )
        self.assertEqual(plan.tool_agent_key, "tool")
        self.assertEqual(plan.rewritten_query, "q rewritten")
        self.assertTrue(plan.answerable)
        mock_client.chat.assert_called_once()
        opts = mock_client.chat.call_args.kwargs.get("options")
        self.assertEqual(opts.response_format, UNIFIED_PLAN_RESPONSE_FORMAT)

    def test_unified_planner_includes_fewshot_messages(self):
        mock_client = mock.Mock()
        mock_client.chat.return_value = mock.Mock(content=_unified_json(answerable=False))
        router = ThinkingRouter(mock_client, "m")
        router.plan_enrich_unified(
            "What is the distance between the Earth and the Moon?",
            has_tools=True,
            available_tools=["tool__geometry_area_circle", "tool__math_factorial"],
            default_tool_agent_key="tool",
        )
        exaone_messages = mock_client.chat.call_args.args[0]
        messages = [{"role": m.role, "content": m.content} for m in exaone_messages]
        self.assertGreaterEqual(len(messages), 4)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        self.assertIn("Earth and the Moon", messages[-1]["content"])

    def test_unified_fallback_to_legacy_on_failure(self):
        mock_client = mock.Mock()
        mock_client.chat.side_effect = [
            RuntimeError("unified fail"),
            mock.Mock(
                content=json.dumps(
                    {
                        "enable_thinking": False,
                        "temperature": 1.0,
                        "top_p": 0.95,
                        "semantic_intent": "general",
                        "confidence": "high",
                        "rationale": "x",
                    }
                )
            ),
            mock.Mock(
                content=json.dumps(
                    {
                        "tool_agent_key": "tool",
                        "rewritten_query": "q",
                        "tool_hints": [],
                    }
                )
            ),
        ]
        router = ThinkingRouter(mock_client, "m")
        plan = router.plan_enrich_unified(
            "hello",
            has_tools=True,
            available_tools=["tool__ping"],
            default_tool_agent_key="tool",
        )
        self.assertEqual(plan.tool_agent_key, "tool")
        self.assertEqual(mock_client.chat.call_count, 3)
        self.assertEqual(
            mock_client.chat.call_args_list[1].kwargs["options"].response_format,
            CLASSIFY_RESPONSE_FORMAT,
        )
        self.assertEqual(
            mock_client.chat.call_args_list[2].kwargs["options"].response_format,
            PLAN_RESPONSE_FORMAT,
        )


if __name__ == "__main__":
    unittest.main()
