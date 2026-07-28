"""
(en) NextStepPlanner: LLM-only enrich loop control (catalog screen, progress evaluation).

No regex or content heuristics — decisions use strict JSON schema LLM calls.
Duplicate tool detection uses canonical JSON equality (deterministic).

(kr) NextStepPlanner입니다. LLM 전용 enrich 루프 제어(catalog screen, progress evaluation)를 수행합니다.

정규식이나 content heuristic은 사용하지 않으며, 결정은 strict JSON schema LLM 호출로 내립니다.
중복 tool 감지는 canonical JSON 동등성(결정적)을 사용합니다.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from exaone.agents.base_agent import ChatHistoryTurn
from exaone.agents.run_trace import AgentRunPhase
from exaone.agents.thinking_router import ThinkingRouter, ToolCallHint
from exaone.agents.thinking_router.llm_json import chat_json
from exaone.tools.results import tool_failure_payload

logger = logging.getLogger(__name__)

_TEMP_MIN = 0.01
_TOP_P_DEFAULT = 0.95

_TOOL_HINT_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "arguments", "reason"],
    "properties": {
        "name": {"type": "string"},
        "arguments": {"type": "object"},
        "reason": {"type": "string"},
    },
}

SCREEN_CATALOG_JSON_SCHEMA: dict[str, Any] = {
    "name": "catalog_screen",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["answerable", "tool_agent_key", "rationale", "suggested_tools"],
        "properties": {
            "answerable": {"type": "boolean"},
            "tool_agent_key": {"type": "string"},
            "rationale": {"type": "string"},
            "suggested_tools": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}

SCREEN_CATALOG_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": SCREEN_CATALOG_JSON_SCHEMA,
}

PROGRESS_JSON_SCHEMA: dict[str, Any] = {
    "name": "progress_evaluation",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["action", "sufficient", "no_progress", "rationale", "next_tool_calls"],
        "properties": {
            "action": {"type": "string", "enum": ["continue_enrich", "finalize"]},
            "sufficient": {"type": "boolean"},
            "no_progress": {"type": "boolean"},
            "rationale": {"type": "string"},
            "next_tool_calls": {
                "type": "array",
                "items": _TOOL_HINT_ITEM_SCHEMA,
            },
        },
    },
}

PROGRESS_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": PROGRESS_JSON_SCHEMA,
}

_SCREEN_SYSTEM = """\
You screen whether the registered ToolAgent tool catalog can help answer the user query.
You receive tool metadata only (qualified name and description), not live results.

Return ONLY one JSON object:
{
  "answerable": true|false,
  "tool_agent_key": "rag|tool|...",
  "rationale": "one short English sentence",
  "suggested_tools": ["tool_agent_key.tool_name", ...]
}

Rules:
- Set answerable=false when abstention/no-tool scope is present in the agent system message.
- Set answerable=false when no tool fits the full request (unrelated, keyword overlap only, wrong scenario, or wrong measurable quantity vs tool output).
- Set answerable=false when the user asks for one quantity or outcome and the tool description computes a different quantity.
- Set answerable=false when the query names symbolic variables without numeric values and catalog tools require numbers.
- Set answerable=true when the user's action matches a catalog tool description end-to-end.
- suggested_tools: qualified catalog names only; at most 2 when answerable=true.
"""

_PROGRESS_SYSTEM = """\
You evaluate progress after one enrich turn of a ToolAgent ReAct loop.
You see the full conversation (roles, content, tool_calls) and the list of tool invocations already attempted.

Return ONLY one JSON object:
{
  "action": "continue_enrich"|"finalize",
  "sufficient": true|false,
  "no_progress": true|false,
  "rationale": "one short English sentence",
  "next_tool_calls": [{"name":"tool_agent_key__tool_name", "arguments": {...}, "reason":"..."}]
}

Rules:
- If sufficient=true OR no_progress=true, set action="finalize" and next_tool_calls=[].
- Do not set sufficient=true while distinct user actions or parameter variants still lack a matching attempted call.
- Prefer continue_enrich when a matching catalog call is missing from attempted invocations.
- Set no_progress=true only after a reasonable matching attempt, repeated empty/failed results, or when the catalog cannot help.
- Abstention/no-tool scope in the system message means finalize with no further tool calls.
- If action="continue_enrich", provide at most ONE next_tool_calls entry (arguments literal from the query; distinct arguments are not duplicates).
"""


class EnrichStopReason(str, Enum):
    SUFFICIENT = "sufficient"
    NO_PROGRESS = "no_progress"
    BUDGET_EXHAUSTED = "budget_exhausted"
    NOT_ANSWERABLE = "not_answerable"
    NO_TOOL_CALLS = "no_tool_calls"
    ERROR = "error"


@dataclass(frozen=True)
class ToolInvocationKey:
    qualified_name: str
    arguments_canonical: str

    @classmethod
    def from_call(cls, qualified_name: str, arguments: dict[str, Any]) -> ToolInvocationKey:
        return cls(
            qualified_name=qualified_name,
            arguments_canonical=json.dumps(arguments, sort_keys=True, ensure_ascii=False),
        )


@dataclass
class ToolInvocationLedger:
    keys: list[ToolInvocationKey] = field(default_factory=list)
    invocation_count: int = 0
    duplicates_blocked: int = 0

    def already_seen(self, key: ToolInvocationKey) -> bool:
        return key in self.keys

    def record(self, key: ToolInvocationKey) -> None:
        self.keys.append(key)
        self.invocation_count += 1

    def attempted_for_planner(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for key in self.keys:
            try:
                args = json.loads(key.arguments_canonical)
            except json.JSONDecodeError:
                args = {}
            out.append({"qualified_name": key.qualified_name, "arguments": args})
        return out


@dataclass
class CatalogScreenResult:
    answerable: bool
    tool_agent_key: str
    rationale: str
    suggested_tools: list[str] = field(default_factory=list)


@dataclass
class ProgressEvaluation:
    action: str
    sufficient: bool
    no_progress: bool
    rationale: str
    next_tool_calls: list[ToolCallHint] = field(default_factory=list)

    @property
    def should_finalize(self) -> bool:
        return (
            self.action == "finalize"
            or self.sufficient
            or self.no_progress
        )


@dataclass
class EnrichRunState:
    ledger: ToolInvocationLedger = field(default_factory=ToolInvocationLedger)
    enrich_turns: int = 0
    stop_reason: EnrichStopReason | None = None
    last_progress: ProgressEvaluation | None = None


def wrap_tool_executor_with_ledger(
    dispatch: Callable[[str, dict[str, Any]], Any],
    ledger: ToolInvocationLedger,
    *,
    max_tool_invocations: int,
) -> Callable[[str, dict[str, Any]], Any]:
    """(en) Deterministic duplicate block and invocation budget (no content heuristics).

    (kr) 결정적 중복 차단과 invocation 예산을 적용합니다(content heuristic 없음).
    """

    def execute(qualified_name: str, arguments: dict[str, Any]) -> Any:
        key = ToolInvocationKey.from_call(qualified_name, arguments)
        if ledger.already_seen(key):
            ledger.duplicates_blocked += 1
            return tool_failure_payload(
                "Duplicate tool invocation blocked.",
                extra={
                    "duplicate": True,
                    "qualified_name": qualified_name,
                    "arguments": arguments,
                },
            )
        if ledger.invocation_count >= max_tool_invocations:
            return tool_failure_payload(
                "Tool invocation budget exhausted.",
                extra={"budget_exhausted": True},
            )
        ledger.record(key)
        return dispatch(qualified_name, arguments)

    return execute


def serialize_messages_for_planner(messages: list[Any]) -> str:
    """(en) Structural serialization (role / tool_calls / content fields only).

    (kr) 구조적 직렬화입니다(role / tool_calls / content 필드만 포함).
    """
    rows: list[dict[str, Any]] = []
    for msg in messages:
        role = getattr(msg, "role", "unknown")
        row: dict[str, Any] = {"role": role}
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            row["tool_calls"] = tool_calls
        else:
            row["content"] = getattr(msg, "content", "") or ""
        rows.append(row)
    return json.dumps(rows, ensure_ascii=False, indent=0)


def append_progress_tool_hint(
    messages: list[Any],
    hint: ToolCallHint,
) -> list[Any]:
    from exaone.llm import ExaoneMessage

    return list(messages) + [
        ExaoneMessage(
            role="user",
            content=(
                "NextStepPlanner suggests one tool call:\n"
                f"- name: {hint.name}\n"
                f"- arguments: {json.dumps(hint.arguments, ensure_ascii=False)}\n"
                f"- reason: {hint.reason or 'n/a'}"
            ),
        )
    ]


class NextStepPlanner:
    """(en) LLM planner for catalog screening and per-turn enrich progress.

    (kr) catalog screening과 턴별 enrich progress용 LLM planner입니다.
    """

    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model
        self._router = ThinkingRouter(client, model)

    @property
    def thinking_router(self) -> ThinkingRouter:
        return self._router

    def screen_catalog(
        self,
        query: str,
        *,
        catalog: list[dict[str, str]],
        history: list[ChatHistoryTurn] | None = None,
    ) -> CatalogScreenResult:
        """LLM screen for answerability. Skipped by ToolAgent when ThinkingRouter is enabled.

        ToolAgent.run calls this only if NextStepPlanner is on and ThinkingRouter is off.
        When both are on, plan_enrich_unified covers catalog/tool choice (one fewer LLM call).
        """
        if not catalog:
            return CatalogScreenResult(
                answerable=False,
                tool_agent_key="tool",
                rationale="empty catalog",
            )
        from exaone.agents.base_agent import BaseAgent

        catalog_text = json.dumps(catalog, ensure_ascii=False, indent=0)
        hist = BaseAgent.normalize_chat_history_turns(history) if history else []
        hist_block = json.dumps(hist, ensure_ascii=False) if hist else "[]"
        user_input = (
            f"Query: {query}\n\n"
            f"Tool catalog (metadata):\n{catalog_text}\n\n"
            f"Recent history:\n{hist_block}"
        )
        try:
            raw = chat_json(
                self._client,
                messages=[
                    {"role": "system", "content": _SCREEN_SYSTEM},
                    {"role": "user", "content": user_input},
                ],
                max_new_tokens=200,
                response_format=SCREEN_CATALOG_RESPONSE_FORMAT,
                phase=AgentRunPhase.CATALOG_SCREEN,
            )
            data = ThinkingRouter._parse_json_object(raw)
            answerable = bool(data.get("answerable", True))
            tool_agent_key = str(data.get("tool_agent_key") or "tool").strip().lower()
            rationale = str(data.get("rationale") or "")
            suggested = [
                str(x).strip()
                for x in (data.get("suggested_tools") or [])
                if str(x).strip()
            ]
            catalog_names = {c["qualified_name"] for c in catalog}
            suggested = [s for s in suggested if s in catalog_names][:2]
            return CatalogScreenResult(
                answerable=answerable,
                tool_agent_key=tool_agent_key,
                rationale=rationale,
                suggested_tools=suggested,
            )
        except Exception as exc:
            # (en) Fully recovered fallback — warn without a stack trace (parse_json_object repairs first).
            # (kr) 완전 복구되는 fallback — 스택트레이스 없이 경고만 남긴다(parse_json_object 가 먼저 복구 시도).
            logger.warning("screen_catalog failed; defaulting to answerable=True (%s)", exc)
            return CatalogScreenResult(
                answerable=True,
                tool_agent_key="tool",
                rationale="screen_catalog_failed_default_answerable",
            )

    def evaluate_progress(
        self,
        query: str,
        *,
        messages: list[Any],
        catalog: list[dict[str, str]],
        ledger: ToolInvocationLedger,
        budget_remaining: dict[str, int],
    ) -> ProgressEvaluation:
        catalog_names = [c["qualified_name"] for c in catalog]
        if not catalog_names:
            return ProgressEvaluation(
                action="finalize",
                sufficient=False,
                no_progress=True,
                rationale="no tools in catalog",
            )
        conversation_json = serialize_messages_for_planner(messages)
        attempted = ledger.attempted_for_planner()
        user_input = (
            f"Query: {query}\n\n"
            f"Budget remaining: {json.dumps(budget_remaining)}\n\n"
            f"Attempted invocations:\n{json.dumps(attempted, ensure_ascii=False)}\n\n"
            f"Tool catalog:\n{json.dumps(catalog, ensure_ascii=False)}\n\n"
            f"Conversation:\n{conversation_json}"
        )
        try:
            raw = chat_json(
                self._client,
                messages=[
                    {"role": "system", "content": _PROGRESS_SYSTEM},
                    {"role": "user", "content": user_input},
                ],
                max_new_tokens=300,
                response_format=PROGRESS_RESPONSE_FORMAT,
                phase=AgentRunPhase.PLANNER_PROGRESS,
            )
            data = ThinkingRouter._parse_json_object(raw)
            action = str(data.get("action") or "finalize").strip().lower()
            if action not in {"continue_enrich", "finalize"}:
                action = "finalize"
            sufficient = bool(data.get("sufficient", False))
            no_progress = bool(data.get("no_progress", False))
            rationale = str(data.get("rationale") or "")
            if sufficient or no_progress:
                action = "finalize"
            hints = _parse_progress_hints(
                data.get("next_tool_calls") or [],
                catalog_names=catalog_names,
                ledger=ledger,
            )
            if action == "finalize":
                hints = []
            return ProgressEvaluation(
                action=action,
                sufficient=sufficient,
                no_progress=no_progress,
                rationale=rationale,
                next_tool_calls=hints,
            )
        except Exception as exc:
            # (en) Fully recovered fallback — warn without a stack trace.
            # (kr) 완전 복구되는 fallback — 스택트레이스 없이 경고만 남긴다.
            logger.warning("evaluate_progress failed; defaulting to finalize (%s)", exc)
            return ProgressEvaluation(
                action="finalize",
                sufficient=False,
                no_progress=True,
                rationale="evaluate_progress_failed",
            )

def _parse_progress_hints(
    items: Any,
    *,
    catalog_names: list[str],
    ledger: ToolInvocationLedger,
) -> list[ToolCallHint]:
    from exaone.agents.tool_agent_catalog import API_TOOL_SEP, normalize_api_tool_name

    allowed = set(catalog_names)
    parsed: list[ToolCallHint] = []
    default_key = "tool"
    if allowed:
        first = next(iter(allowed))
        default_key = first.split(API_TOOL_SEP, 1)[0] if API_TOOL_SEP in first else "tool"
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        api_name = normalize_api_tool_name(name, default_tool_agent_key=default_key)
        if api_name not in allowed:
            continue
        name = api_name
        args = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
        key = ToolInvocationKey.from_call(name, args)
        if ledger.already_seen(key):
            continue
        reason = str(item.get("reason") or "")
        parsed.append(ToolCallHint(name=name, arguments=args, reason=reason))
        if len(parsed) >= 1:
            break
    return parsed
