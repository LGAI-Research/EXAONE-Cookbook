"""
(en) Per-run LLM call tracing for ToolAgent (phase, schema, latency).

Activate via set_active_llm_trace() for the duration of ToolAgent.run(); router,
planner, and base_agent record through traced_chat() when a trace is active.

(kr) ToolAgent run 단위 LLM 호출 추적(phase, schema, latency)입니다.
ToolAgent.run() 동안 set_active_llm_trace()로 활성화하고, router/planner/base_agent가
traced_chat()으로 기록합니다.
"""
from __future__ import annotations

import logging
import time
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from exaone.llm import ExaoneGenerateOptions, ExaoneMessage

logger = logging.getLogger(__name__)


class AgentRunPhase(str, Enum):
    """LLM call phases within a ToolAgent run (for llm_calls metadata)."""

    CATALOG_SCREEN = "catalog_screen"
    ROUTE_CLASSIFY = "route_classify"
    ROUTE_PLAN_ENRICH = "route_plan_enrich"
    ROUTE_PLAN_ENRICH_UNIFIED = "route_plan_enrich_unified"
    ROUTE_PLAN_FINALIZE = "route_plan_finalize"
    PLANNER_PROGRESS = "planner_progress"
    ENRICH_REACT = "enrich_react"
    FINAL_ANSWER = "final_answer"


@dataclass
class LlmCallRecord:
    phase: str
    schema_name: str = ""
    latency_ms: float = 0.0
    enable_thinking: bool = False
    has_tools: bool = False
    turn: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "phase": self.phase,
            "latency_ms": round(self.latency_ms, 2),
        }
        if self.schema_name:
            out["schema_name"] = self.schema_name
        if self.enable_thinking:
            out["enable_thinking"] = True
        if self.has_tools:
            out["has_tools"] = True
        if self.turn is not None:
            out["turn"] = self.turn
        return out


@dataclass
class LlmCallTrace:
    records: list[LlmCallRecord] = field(default_factory=list)

    def record(self, entry: LlmCallRecord) -> None:
        self.records.append(entry)
        logger.debug(
            "llm_call phase=%s schema=%s latency_ms=%.1f",
            entry.phase,
            entry.schema_name or "-",
            entry.latency_ms,
        )

    def to_metadata_list(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.records]

    @property
    def call_count(self) -> int:
        return len(self.records)


_active_trace: ContextVar[LlmCallTrace | None] = ContextVar("llm_call_trace", default=None)


def get_active_llm_trace() -> LlmCallTrace | None:
    return _active_trace.get()


def set_active_llm_trace(trace: LlmCallTrace) -> Token:
    return _active_trace.set(trace)


def reset_active_llm_trace(token: Token) -> None:
    _active_trace.reset(token)


def schema_name_from_response_format(response_format: dict[str, Any] | None) -> str:
    if not response_format:
        return ""
    js = response_format.get("json_schema") or {}
    return str(js.get("name") or "")


def traced_chat(
    client: Any,
    messages: list[ExaoneMessage],
    options: ExaoneGenerateOptions | None,
    *,
    phase: AgentRunPhase | str,
    schema_name: str = "",
    turn: int | None = None,
) -> Any:
    """Invoke client.chat and append to the active LlmCallTrace when set."""
    opts = options or ExaoneGenerateOptions()
    if not schema_name:
        schema_name = schema_name_from_response_format(
            getattr(opts, "response_format", None)
        )
    phase_str = phase.value if isinstance(phase, AgentRunPhase) else str(phase)
    t0 = time.perf_counter()
    resp = client.chat(messages, options=opts)
    latency_ms = getattr(resp, "latency_ms", None)
    if latency_ms is None:
        latency_ms = (time.perf_counter() - t0) * 1000.0
    trace = get_active_llm_trace()
    if trace is not None:
        trace.record(
            LlmCallRecord(
                phase=phase_str,
                schema_name=schema_name,
                latency_ms=float(latency_ms),
                enable_thinking=bool(getattr(opts, "enable_thinking", False)),
                has_tools=bool(getattr(opts, "tools", None)),
                turn=turn,
            )
        )
    return resp
