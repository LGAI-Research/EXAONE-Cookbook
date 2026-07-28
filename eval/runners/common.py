"""
(en) Shared utilities for naive and harness runners.

The two pieces both runners need:

1. **Function-schema wrapping**: each `ToolSpec` is wrapped into the
   OpenAI/Friendli `{"type": "function", "function": {...}}` envelope.
2. **Call capture**: a `CapturedExecutor` records every (name, arguments) pair
   the model produced. This is what populates `TrialResult.tool_calls`.

Notes on the harness path:

- We subclass `exaone.tools.ToolRegistry` to skip `jsonschema` argument
  validation. BFCL parameter schemas use BFCL-specific types ("float", "tuple",
  "any") that are not strict JSON Schema; validation would reject otherwise valid
  evaluation calls before they reach our capture hook. We still want the LLM to
  see the original schema (so it can reason about types), so the schema is
  preserved on the Tool; only validation is loosened.

(kr) naive / harness runner가 공유하는 유틸리티이다.

두 runner가 모두 필요한 부분:

1. **function-schema 래핑**: 각 `ToolSpec`을 OpenAI/Friendli의
   `{"type": "function", "function": {...}}` envelope로 감싼다.
2. **호출 캡처**: `CapturedExecutor`가 모델이 만든 (name, arguments) 쌍을 모두 기록한다.
   이 결과가 `TrialResult.tool_calls`를 채운다.

하네스 경로 주의:

- `exaone.tools.ToolRegistry`를 서브클래싱해 `jsonschema` 인자 검증을 우회한다.
  BFCL 파라미터 스키마는 BFCL 고유 타입("float", "tuple", "any")을 사용하므로 엄격 JSON Schema
  검증을 적용하면 캡처 hook에 도달하기 전에 호출이 거부된다. LLM에는 원본 스키마를 그대로
  노출해야 추론이 정확하므로 스키마 자체는 보존하고 검증만 완화한다.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from eval.datasets.schema import EvalTask, ToolSpec
from eval.metrics.types import ToolCallRecord, TrialResult

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful agent operating in an evaluation setting with optional tools.\n"
    "Instruction priority:\n"
    "1. Abstention or no-tool scope when present in this system message (overrides tool use).\n"
    "2. Tool-trajectory scope when present (catalog action required).\n"
    "3. General rules below.\n"
    "Rules:\n"
    "- Read each tool's name and description in the catalog. When the user's request "
    "matches a tool's described capability end-to-end, call that tool with well-formed JSON arguments.\n"
    "- Take argument values literally from the user message (numbers, names, IDs, dates, "
    "times, units). Do not paraphrase, round, reformat, or substitute different entities.\n"
    "- When the user gives a percentage rate and the tool expects a fractional rate, "
    "pass the decimal form (e.g. 4% annual interest → 0.04).\n"
    "- If the request implies multiple distinct tool actions, make each required call; "
    "do not replace tool use with a prose-only answer when a catalog tool should run.\n"
    "- If no provided tool applies to the full request, answer directly without calling any tool.\n"
    "- A similar tool name or partial topic overlap is not enough to call a tool.\n"
    "- When a constraint applies to the whole request (sorting, filtering, ranking, etc.), "
    "reflect it in every matching tool call's arguments — not only the last call.\n"
    "- Use only tools listed in the catalog; do not invent tool names."
)

TOOL_TRAJECTORY_APPENDIX = (
    "\n\nTool-trajectory task (catalog action required):\n"
    "- Success requires invoking the catalog tool(s) whose description matches the "
    "user's requested action end-to-end.\n"
    "- Call the matching tool(s) before giving a final natural-language answer.\n"
    "- Read each tool's parameter schema and descriptions; pass values that match the "
    "expected types (e.g. when the user gives a percentage and the schema expects a "
    "fractional rate, use the decimal form such as 4% annual interest → 0.04).\n"
    "- Copy argument values directly from the user query; keep spelling, casing, time "
    "phrasing, and numeric literals faithful — do not round or reformat.\n"
    "- Comma-separated lists of periods or variants mean separate calls for each listed value.\n"
    "- When several independent actions are requested, issue a separate matching call "
    "for each; order does not matter unless the user specifies otherwise.\n"
    "- When multiple calls share the same tool name but different arguments, include every "
    "required variant in one assistant turn (parallel tool_calls) instead of one call at a time.\n"
    "- When the user pairs distinct entities with distinct parameters (each title with its "
    "own time, each period with its own value, etc.), issue separate tool calls with scalar "
    "arguments per pair — do not merge pairs into one call using parallel arrays unless the "
    "schema explicitly models a single batch request.\n"
    "- When the user asks for multiple facts about the same entity, make separate matching "
    "calls using the parameter variants the tool schema provides.\n"
    "- When sorting, filtering, ranking, or similar constraints apply to several entities "
    "or services in one request, set the matching boolean, enum, or flag parameters on "
    "every relevant catalog call — not only on the last call.\n"
    "- This scope applies only when abstention/no-tool scope is not also present above."
)

ABSTENTION_APPENDIX = (
    "\n\nAbstention task (no tool should be used):\n"
    "- None of the provided tools correctly apply to the full user request.\n"
    "- Success requires zero tool calls in the trajectory; answer directly in finalize, "
    "even when a catalog entry looks related by name or topic.\n"
    "- Do not invoke a tool merely because it appears in the catalog or shares keywords with the question.\n"
    "- If the user asks for one measurable quantity or outcome and a tool description "
    "computes a different quantity, abstain — keyword overlap is not enough.\n"
    "- Symbolic variables in the question (e.g. t, v, r, I) without concrete numbers "
    "usually mean no catalog tool can run — abstain.\n"
    "- This scope overrides any tool-trajectory, router hint, or general tool-use instruction."
)


def is_tool_trajectory_task(task: EvalTask) -> bool:
    """
    (en) True when the task carries gold tool trajectory metadata (any loader).

    Uses ``expected_tool_calls`` or ``metadata['bfcl_ground_truth']`` — never
    dataset name strings.

    (kr) gold tool trajectory 메타가 있으면 True. ``expected_tool_calls`` 또는
    ``metadata['bfcl_ground_truth']``만 보며 dataset 이름 문자열은 쓰지 않는다.
    """
    if task.expected_tool_calls:
        return True
    return bool(task.metadata.get("bfcl_ground_truth"))


def is_abstention_task(task: EvalTask) -> bool:
    """
    (en) True when the task expects no tool calls (e.g. irrelevance / M5 gold).

    (kr) tool 호출이 없어야 하는 태스크(예: irrelevance / M5 gold)이면 True.
    """
    return bool(task.expected_no_tools)


def harness_agent_options(task: EvalTask) -> dict[str, bool]:
    """
    (en) Default ThinkingRouter / NextStepPlanner toggles for harness eval runs.

    Tier-3 ``system_prompt_for`` appendices (abstention, tool-trajectory) are visible
    to naive and to ToolAgent enrich, but ``ThinkingRouter.plan_enrich_unified`` only
    receives the user query and tool names. Disable router on scoped tasks; for
    abstention, enable planner catalog screen only (no router) so enrich can skip
    when the catalog does not fit end-to-end.

    (kr) harness eval용 ThinkingRouter / NextStepPlanner 기본 토글.

    Tier-3 ``system_prompt_for`` appendix(abstention, tool-trajectory)는 naive와
    ToolAgent enrich에 보이지만 ``ThinkingRouter.plan_enrich_unified``에는 user query와
    tool 이름만 전달된다. scope 태스크에서는 router를 끈다. abstention에서는 planner
    catalog screen만 켜 enrich skip을 허용하고, tool-trajectory에서는 planner도 끈다.
    """
    if task.system_prompt:
        return {"use_thinking_router": True, "use_next_step_planner": True}
    if is_abstention_task(task):
        return {"use_thinking_router": False, "use_next_step_planner": True}
    if is_tool_trajectory_task(task):
        return {"use_thinking_router": False, "use_next_step_planner": False}
    return {"use_thinking_router": True, "use_next_step_planner": True}


def system_prompt_for(task: EvalTask, *, default: str = DEFAULT_SYSTEM_PROMPT) -> str:
    """
    (en) Resolve the system prompt for naive and harness runners. Custom
    ``task.system_prompt`` wins unchanged. Otherwise compose shared base + optional
    appendices from task schema fields (Tier 3).

    (kr) naive/harness 공통 system prompt. ``task.system_prompt``가 있으면 그대로.
    없으면 공통 base + schema 필드 기반 appendix(Tier 3)를 조합한다.
    """
    if task.system_prompt:
        return task.system_prompt
    parts = [default]
    if is_tool_trajectory_task(task):
        parts.append(TOOL_TRAJECTORY_APPENDIX)
    if is_abstention_task(task):
        parts.append(ABSTENTION_APPENDIX)
    return "".join(parts)


def to_function_schema(tool: ToolSpec) -> dict[str, Any]:
    """
    (en) Wrap a `ToolSpec` into the OpenAI/Friendli tool envelope.

    (kr) `ToolSpec`을 OpenAI/Friendli tool envelope로 감싼다.
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.parameters or {"type": "object", "properties": {}},
        },
    }


def tools_to_schemas(tools: list[ToolSpec]) -> list[dict[str, Any]]:
    return [to_function_schema(t) for t in tools]


@dataclass
class CapturedExecutor:
    """
    (en) Stateful tool executor: records every call, returns a deterministic stub
    result so the agent loop keeps making progress.

    A non-None `task_id` is only used for log breadcrumbs; the captured calls
    live on `self.calls` and are read after the run.

    (kr) 상태 보존형 도구 실행자. 모든 호출을 기록하고 결정론적 stub 결과를 돌려줘
    에이전트 루프가 멈추지 않게 한다.

    `task_id`는 로그 식별용일 뿐이며 캡처된 호출은 `self.calls`에 누적되고 run 종료 후
    조회한다.
    """

    task_id: str = ""
    calls: list[ToolCallRecord] = field(default_factory=list)

    def __call__(self, name: str, arguments: dict[str, Any]) -> Any:
        t0 = time.monotonic()
        args = arguments if isinstance(arguments, dict) else {}
        record = ToolCallRecord(
            name=name,
            arguments=args,
            latency_ms=(time.monotonic() - t0) * 1000,
            result_repr='{"ok": true, "note": "captured-stub"}',
        )
        self.calls.append(record)
        return {"ok": True, "note": "captured-stub", "echo": args}


def build_capturing_registry(
    tools: list[ToolSpec],
    *,
    task_id: str = "",
) -> tuple[Any, CapturedExecutor]:
    """
    (en) Build a `CapturingToolRegistry` plus the shared `CapturedExecutor`.
    Lazy-imports `exaone.tools` so the module is importable without the harness
    (e.g. in tests of the naive runner only).

    (kr) `CapturingToolRegistry`와 공유 `CapturedExecutor`를 생성한다. `exaone.tools`를
    lazy import하여 하네스 미설치 환경(naive runner 단독 테스트 등)에서도 import 가능하다.
    """
    from exaone.tools import Tool, ToolRegistry
    from exaone.tools.results import tool_failure_payload

    class _CapturingToolRegistry(ToolRegistry):
        def execute(self, name: str, arguments: dict[str, Any]) -> Any:
            tool = self.get(name)
            if tool is None:
                return tool_failure_payload(f"Unknown tool: {name}", guidance=None)
            try:
                return tool.run(arguments)
            except Exception as e:
                logger.exception("Captured tool execution failed: %s", name)
                return tool_failure_payload(str(e))

    executor = CapturedExecutor(task_id=task_id)
    registry = _CapturingToolRegistry()
    for spec in tools:
        schema = to_function_schema(spec)

        def _make_exec(tool_name: str):
            def _run(arguments: dict[str, Any]) -> Any:
                return executor(tool_name, arguments)
            return _run

        registry.register(Tool(name=spec.name, schema=schema, execute=_make_exec(spec.name)))
    return registry, executor


def normalize_tool_call_args(raw: Any) -> dict[str, Any]:
    """
    (en) OpenAI/Friendli emits ``function.arguments`` as a JSON string. Parse it
    leniently; on failure, return ``{}`` and log a warning. Already-parsed dicts
    pass through.

    (kr) OpenAI/Friendli는 ``function.arguments``를 JSON 문자열로 내보낸다. 관대하게
    파싱하고, 실패 시 ``{}``와 경고. 이미 dict면 그대로 반환.
    """
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        try:
            parsed = json.loads(s)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            logger.warning("Failed to parse tool_call arguments JSON: %r", s[:200])
            return {}
    return {}


def user_content_for(task: EvalTask) -> str:
    """
    (en) User message body. When ``grounding_context`` is set (HaluBench / RAG eval),
    prepend the passage so M9 can score grounded answers.

    (kr) user 메시지 본문. ``grounding_context``가 있으면(HaluBench/RAG eval) passage를
    앞에 붙여 M9 grounded 답변 채점이 가능하게 한다.
    """
    ctx = (task.grounding_context or "").strip()
    if not ctx:
        return task.query
    return (
        "Use the following context when answering. "
        "Answer only with facts supported by the context.\n\n"
        f"Context:\n{ctx}\n\n"
        f"Question:\n{task.query}"
    )


def make_trial(
    *,
    task: EvalTask,
    runner: str,
    trial_id: str,
    final_content: str,
    final_structured: Any,
    captured_calls: list[ToolCallRecord],
    turns: int,
    input_tokens: int,
    output_tokens: int,
    total_latency_ms: float,
    finished: bool,
    error: str | None,
    metadata: dict[str, Any] | None = None,
) -> TrialResult:
    """
    (en) Single chokepoint where both runners assemble the unified `TrialResult`.

    (kr) 두 runner가 통합 `TrialResult`를 조립하는 단일 합류 지점.
    """
    return TrialResult(
        trial_id=trial_id,
        task_id=task.task_id,
        dataset=task.dataset,
        runner=runner,
        final_content=final_content,
        final_structured=final_structured,
        tool_calls=list(captured_calls),
        turns=int(turns),
        input_tokens=int(input_tokens),
        output_tokens=int(output_tokens),
        total_latency_ms=float(total_latency_ms),
        finished=finished,
        error=error,
        metadata=dict(metadata or {}),
    )


def retry_on_429(
    call,
    *,
    max_attempts: int = 5,
    base_delay: float = 2.0,
    is_429,
):
    """
    (en) Identical 429 backoff used by both naive and harness LLM layers so
    rate-limit handling never leaks into the harness-vs-naive comparison.

    Exponential backoff: `base_delay * 2 ** attempt`. Re-raises any non-429
    exception immediately and the final 429 if all attempts exhaust.

    (kr) naive·harness LLM 계층이 공유하는 동일 429 backoff. rate-limit 처리 차이가
    하네스 vs naive 비교에 새지 않게 한다. exponential backoff(`base_delay * 2 ** attempt`).
    429가 아닌 예외는 즉시 재전파; 모든 시도 소진 시 마지막 429 재전파.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return call()
        except Exception as e:
            if not is_429(e):
                raise
            last_exc = e
            if attempt + 1 == max_attempts:
                break
            delay = base_delay * (2 ** attempt)
            logger.warning("LLM 429 — backoff %.1fs (attempt %d/%d)", delay, attempt + 1, max_attempts)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


__all__ = [
    "DEFAULT_SYSTEM_PROMPT",
    "TOOL_TRAJECTORY_APPENDIX",
    "ABSTENTION_APPENDIX",
    "is_tool_trajectory_task",
    "is_abstention_task",
    "harness_agent_options",
    "to_function_schema",
    "tools_to_schemas",
    "CapturedExecutor",
    "build_capturing_registry",
    "normalize_tool_call_args",
    "system_prompt_for",
    "user_content_for",
    "make_trial",
    "retry_on_429",
]
