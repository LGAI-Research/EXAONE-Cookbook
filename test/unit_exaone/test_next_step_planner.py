"""Tests for NextStepPlanner ledger and LLM progress/screen paths."""

from __future__ import annotations

import json
import unittest
import unittest.mock

from exaone.agents.next_step_planner import (
    NextStepPlanner,
    ToolInvocationKey,
    ToolInvocationLedger,
    wrap_tool_executor_with_ledger,
)
from exaone.tools.results import is_tool_failure_payload


class TestToolInvocationLedger(unittest.TestCase):
    def test_duplicate_key_detected_by_canonical_args(self):
        ledger = ToolInvocationLedger()
        k1 = ToolInvocationKey.from_call("rag.retrieve", {"query": "a", "top_k": 3})
        k2 = ToolInvocationKey.from_call("rag.retrieve", {"top_k": 3, "query": "a"})
        self.assertFalse(ledger.already_seen(k1))
        ledger.record(k1)
        self.assertTrue(ledger.already_seen(k2))

    def test_wrap_blocks_duplicate_and_increments_counter(self):
        ledger = ToolInvocationLedger()
        calls: list[tuple[str, dict]] = []

        def dispatch(name: str, args: dict) -> str:
            calls.append((name, args))
            return "ok"

        wrapped = wrap_tool_executor_with_ledger(
            dispatch, ledger, max_tool_invocations=5
        )
        wrapped("tool.search", {"q": "x"})
        second = wrapped("tool.search", {"q": "x"})
        self.assertEqual(len(calls), 1)
        self.assertEqual(ledger.duplicates_blocked, 1)
        self.assertTrue(is_tool_failure_payload(second))
        self.assertTrue(second.get("duplicate"))

    def test_budget_exhausted_without_dispatch(self):
        ledger = ToolInvocationLedger()
        wrapped = wrap_tool_executor_with_ledger(
            lambda n, a: "ok", ledger, max_tool_invocations=1
        )
        wrapped("tool.a", {})
        out = wrapped("tool.b", {})
        self.assertEqual(ledger.invocation_count, 1)
        self.assertIn("budget", str(out).lower() + json.dumps(out))


class TestNextStepPlannerLLM(unittest.TestCase):
    def _chat_response(self, content: str) -> unittest.mock.Mock:
        return unittest.mock.Mock(content=content)

    def test_screen_catalog_not_answerable(self):
        mock_client = unittest.mock.Mock()
        mock_client.chat.return_value = self._chat_response(
            json.dumps(
                {
                    "answerable": False,
                    "tool_agent_key": "tool",
                    "rationale": "no relevant tools",
                    "suggested_tools": [],
                }
            )
        )
        planner = NextStepPlanner(mock_client, "m")
        result = planner.screen_catalog(
            "tell me a joke",
            catalog=[{"qualified_name": "tool.weather", "description": "weather"}],
        )
        self.assertFalse(result.answerable)

    def test_evaluate_progress_finalize_on_no_progress(self):
        mock_client = unittest.mock.Mock()
        mock_client.chat.return_value = self._chat_response(
            json.dumps(
                {
                    "action": "finalize",
                    "sufficient": False,
                    "no_progress": True,
                    "rationale": "tools cannot help",
                    "next_tool_calls": [],
                }
            )
        )
        planner = NextStepPlanner(mock_client, "m")
        ledger = ToolInvocationLedger()
        ledger.record(ToolInvocationKey.from_call("tool.search", {"q": "x"}))
        progress = planner.evaluate_progress(
            "obscure question",
            messages=[unittest.mock.Mock(role="user", content="obscure question", tool_calls=None)],
            catalog=[{"qualified_name": "tool.search", "description": "search"}],
            ledger=ledger,
            budget_remaining={"enrich_turns_remaining": 3, "tool_invocations_remaining": 2},
        )
        self.assertTrue(progress.should_finalize)
        self.assertTrue(progress.no_progress)

    def test_evaluate_progress_skips_duplicate_hint(self):
        mock_client = unittest.mock.Mock()
        mock_client.chat.return_value = self._chat_response(
            json.dumps(
                {
                    "action": "continue_enrich",
                    "sufficient": False,
                    "no_progress": False,
                    "rationale": "retry",
                    "next_tool_calls": [
                        {
                            "name": "tool.search",
                            "arguments": {"q": "same"},
                            "reason": "again",
                        }
                    ],
                }
            )
        )
        planner = NextStepPlanner(mock_client, "m")
        ledger = ToolInvocationLedger()
        ledger.record(ToolInvocationKey.from_call("tool.search", {"q": "same"}))
        progress = planner.evaluate_progress(
            "q",
            messages=[],
            catalog=[{"qualified_name": "tool.search", "description": "search"}],
            ledger=ledger,
            budget_remaining={"enrich_turns_remaining": 5, "tool_invocations_remaining": 5},
        )
        self.assertEqual(progress.next_tool_calls, [])


if __name__ == "__main__":
    unittest.main()
