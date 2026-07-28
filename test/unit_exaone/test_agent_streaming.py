"""Tests for AgentEvent → SSE transport helpers."""
from __future__ import annotations

import json

from exaone.agents.events import AgentEvent
from exaone.agents.streaming import agent_event_to_sse, iter_agent_events_as_sse


def test_agent_event_to_sse_format():
    ev = AgentEvent(type="turn_start", turn=1, payload={"step": "reason"})
    out = agent_event_to_sse(ev)
    assert out.startswith("event: turn_start\n")
    assert "data: " in out
    payload = json.loads(out.split("data: ", 1)[1].strip())
    assert payload["type"] == "turn_start"
    assert payload["turn"] == 1


def test_phase_event_sse():
    ev = AgentEvent(
        type="phase_start",
        turn=0,
        payload={"phase": "enrich", "max_turns": 3},
    )
    out = agent_event_to_sse(ev)
    assert out.startswith("event: phase_start\n")
    payload = json.loads(out.split("data: ", 1)[1].strip())
    assert payload["payload"]["phase"] == "enrich"


def test_iter_agent_events_as_sse():
    events = [
        AgentEvent(type="run_start", turn=0),
        AgentEvent(type="run_end", turn=1, payload={"final_content": "x"}),
    ]
    lines = list(iter_agent_events_as_sse(iter(events)))
    assert len(lines) == 2
    assert all(line.endswith("\n\n") for line in lines)
