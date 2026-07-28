"""PR2: plan_finalize reuses enrich RouteDecision without a second route() LLM call."""
from __future__ import annotations

import unittest
from unittest import mock


from exaone.agents.thinking_router.policy import finalize_decision_from_enrich
from exaone.agents.thinking_router.router import ThinkingRouter
from exaone.agents.thinking_router.schemas import FINALIZE_RESPONSE_FORMAT, ROUTER_OUTPUT_FORMAT
from exaone.agents.thinking_router.types import RouteDecision


def _enrich_decision() -> RouteDecision:
    return RouteDecision(
        enable_thinking=True,
        temperature=0.8,
        top_p=0.9,
        final_response_format=ROUTER_OUTPUT_FORMAT,
        semantic_intent="analytical",
    )


class TestFinalizeDecisionFromEnrich(unittest.TestCase):
    def test_finalize_policy_tools_off(self):
        out = finalize_decision_from_enrich(_enrich_decision(), has_context=True)
        self.assertEqual(out.temperature, 0.8)
        self.assertEqual(out.semantic_intent, "analytical")
        # has_tools=False: thinking follows enrich axes, not forced on by tools policy
        self.assertTrue(out.enable_thinking)


class TestPlanFinalizeSkipsRoute(unittest.TestCase):
    def test_plan_finalize_with_enrich_decision_skips_route(self):
        mock_client = mock.Mock()
        mock_client.chat.return_value = mock.Mock(
            content='{"answer_tool_agent_key":"rag","rewritten_query":"q"}'
        )
        router = ThinkingRouter(mock_client, "m")
        with mock.patch.object(router, "route") as mock_route:
            plan = router.plan_finalize(
                "question",
                has_context=True,
                enrich_decision=_enrich_decision(),
                default_answer_tool_agent="answer",
            )
        mock_route.assert_not_called()
        self.assertEqual(plan.answer_tool_agent_key, "rag")
        mock_client.chat.assert_called_once()
        opts = mock_client.chat.call_args.kwargs.get("options")
        self.assertEqual(opts.response_format, FINALIZE_RESPONSE_FORMAT)

    def test_plan_finalize_without_enrich_decision_calls_route(self):
        mock_client = mock.Mock()
        mock_client.chat.return_value = mock.Mock(
            content='{"answer_tool_agent_key":"answer","rewritten_query":"q"}'
        )
        router = ThinkingRouter(mock_client, "m")
        enrich_axes = _enrich_decision()
        with mock.patch.object(router, "route", return_value=enrich_axes) as mock_route:
            router.plan_finalize("question", has_context=False)
        mock_route.assert_called_once()


if __name__ == "__main__":
    unittest.main()
