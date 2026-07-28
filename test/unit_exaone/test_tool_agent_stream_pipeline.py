"""ToolAgent: run_stream aligned with run(); phase events and streaming flags.

run_stream 이 run 과 동일한 단계·스트리밍 플래그를 따르는지 검증한다.
"""
from __future__ import annotations

import unittest
from unittest import mock


from exaone.agents.base_agent import AgentContext
from exaone.agents.tool_agent import PHASE_ENRICH, PHASE_FINALIZE, PHASE_PREFLIGHT, ToolAgent
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


class TestToolAgentStreamPipeline(unittest.TestCase):
    def test_run_stream_emits_phase_events(self):
        llm = mock.Mock()
        llm.model = "test-model"
        llm.chat.return_value = ExaoneResponse(
            content='{"answer":"ok","confidence":"high"}',
            tool_calls=None,
        )

        agent = ToolAgent(
            tool_registry=_minimal_registry(),
            use_thinking_router=False,
            use_next_step_planner=False,
            max_enrich_turns=1,
        )

        events = list(
            agent.run_stream(AgentContext(query="hi"), llm=llm, stream_llm=False)
        )
        types = [e.type for e in events]
        self.assertIn("run_start", types)
        self.assertIn("phase_start", types)
        self.assertIn("phase_end", types)
        self.assertIn("run_end", types)
        phases_started = [
            e.payload.get("phase")
            for e in events
            if e.type == "phase_start"
        ]
        self.assertIn(PHASE_ENRICH, phases_started)
        self.assertIn(PHASE_FINALIZE, phases_started)

    def test_stream_enrich_reasoning_passed_to_enrich_loop(self):
        llm = mock.Mock()
        llm.model = "test-model"

        agent = ToolAgent(
            tool_registry=_minimal_registry(),
            use_thinking_router=False,
            use_next_step_planner=False,
            max_enrich_turns=1,
        )

        captured: list[bool] = []

        def _fake_iter(*_a, stream_llm=False, **_kw):
            captured.append(stream_llm)
            yield mock.Mock(type="run_start", turn=0, payload={})
            yield mock.Mock(
                type="run_end",
                turn=1,
                payload={"final_content": "", "messages": [], "error": None},
            )

        with mock.patch.object(ToolAgent, "_iter_reason_tool_loop", side_effect=_fake_iter):
            list(
                agent.run_stream(
                    AgentContext(query="hi"),
                    llm=llm,
                    stream_llm=True,
                    stream_enrich_reasoning=True,
                )
            )
        self.assertEqual(captured, [True])

        captured.clear()
        with mock.patch.object(ToolAgent, "_iter_reason_tool_loop", side_effect=_fake_iter):
            list(
                agent.run_stream(
                    AgentContext(query="hi"),
                    llm=llm,
                    stream_llm=True,
                    stream_enrich_reasoning=False,
                )
            )
        self.assertEqual(captured, [False])

    def test_preflight_planner_screen_emits_planner_end(self):
        llm = mock.Mock()
        llm.model = "test-model"
        llm.chat.return_value = ExaoneResponse(
            content='{"answer":"ok","confidence":"high"}',
            tool_calls=None,
        )

        agent = ToolAgent(
            tool_registry=_minimal_registry(),
            use_thinking_router=False,
            use_next_step_planner=True,
            max_enrich_turns=1,
        )
        from exaone.agents.next_step_planner import CatalogScreenResult

        planner = mock.Mock()
        planner.screen_catalog.return_value = CatalogScreenResult(
            answerable=True,
            tool_agent_key="tool",
            rationale="ok",
        )
        planner.evaluate_progress = mock.Mock()
        agent._get_next_step_planner = mock.Mock(return_value=planner)  # type: ignore[method-assign]

        with mock.patch.object(
            agent,
            "_iter_reason_tool_loop",
            return_value=iter(
                [
                    mock.Mock(type="run_start", turn=0, payload={}),
                    mock.Mock(
                        type="run_end",
                        turn=1,
                        payload={"final_content": "", "messages": [], "error": None},
                    ),
                ]
            ),
        ):
            events = list(
                agent.run_stream(AgentContext(query="hi"), llm=llm, stream_llm=False)
            )

        planner_ends = [e for e in events if e.type == "planner_end"]
        self.assertTrue(planner_ends)
        self.assertEqual(planner_ends[0].payload.get("kind"), "catalog_screen")
        preflight = [
            e for e in events if e.type == "phase_start" and e.payload.get("phase") == PHASE_PREFLIGHT
        ]
        self.assertEqual(len(preflight), 1)


if __name__ == "__main__":
    unittest.main()
