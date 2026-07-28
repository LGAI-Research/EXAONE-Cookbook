"""PR3: LlmCallTrace records router/planner/react/finalize phases."""
from __future__ import annotations

import unittest
from unittest import mock


from exaone.agents.run_trace import (
    AgentRunPhase,
    LlmCallTrace,
    reset_active_llm_trace,
    set_active_llm_trace,
    traced_chat,
)
from exaone.llm import ExaoneGenerateOptions, ExaoneMessage, ExaoneResponse


class TestLlmCallTrace(unittest.TestCase):
    def test_traced_chat_records_when_active(self):
        trace = LlmCallTrace()
        token = set_active_llm_trace(trace)
        client = mock.Mock()
        client.chat.return_value = ExaoneResponse(content="{}", latency_ms=12.5)
        try:
            traced_chat(
                client,
                [ExaoneMessage(role="user", content="hi")],
                ExaoneGenerateOptions(max_new_tokens=10),
                phase=AgentRunPhase.ROUTE_CLASSIFY,
                schema_name="route_axes",
            )
        finally:
            reset_active_llm_trace(token)
        self.assertEqual(trace.call_count, 1)
        self.assertEqual(trace.records[0].phase, "route_classify")
        self.assertEqual(trace.records[0].schema_name, "route_axes")

    def test_traced_chat_noop_without_active_trace(self):
        client = mock.Mock()
        client.chat.return_value = ExaoneResponse(content="ok", latency_ms=1.0)
        traced_chat(
            client,
            [ExaoneMessage(role="user", content="hi")],
            None,
            phase=AgentRunPhase.FINAL_ANSWER,
        )
        client.chat.assert_called_once()


if __name__ == "__main__":
    unittest.main()
