"""
(en) Agent-level semantic events (turn / tool / LLM delta).
Independent of provider SSE wire format; see exaone.llm.streaming for provider adapters.

(kr) Agent 수준 semantic 이벤트입니다(turn / tool / LLM delta).
provider SSE wire 형식과 독립적이며, provider adapter는 exaone.llm.streaming을 참고합니다.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AgentEventType = Literal[
    "run_start",
    "phase_start",
    "phase_end",
    "planner_end",
    "turn_start",
    "llm_delta",
    "llm_end",
    "tool_start",
    "tool_end",
    "run_end",
    "error",
]


@dataclass(frozen=True)
class AgentEvent:
    type: AgentEventType
    turn: int = 0
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
