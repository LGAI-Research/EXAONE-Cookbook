"""
(en) Harness runner — wraps `exaone.agents.ToolAgent.run()` so the same
`EvalTask` produces a `TrialResult` directly comparable to the naive baseline.

All harness affordances are active by default:

- `ExaoneAPIClient` empty-200 / reasoning-only recovery (thinking off → nudge).
- `ToolInvocationLedger` duplicate suppression (canonical JSON args).
- `ThinkingRouter` + `NextStepPlanner` enrich → finalize phases.
- `StructuredOutputPipeline` (`JsonExtractor → AutoRepair → SchemaValidator`)
  applied during `ToolAgent` finalize.

The runner injects a `CapturingToolRegistry` (see `runners/common.py`) so every
tool call the agent makes is recorded into `TrialResult.tool_calls`. Token
counts and turn counts come from `AgentResult.metadata` keys that the harness
already populates via `exaone.observability.fields`.

(kr) 하네스 runner. `exaone.agents.ToolAgent.run()`을 래핑해 같은 `EvalTask`로 naive
baseline과 직접 비교 가능한 `TrialResult`를 산출한다.

기본으로 하네스 보조 기능 전부 활성화:

- `ExaoneAPIClient` 빈 200/reasoning-only 복구(thinking off → nudge).
- `ToolInvocationLedger` 중복 호출 차단(canonical JSON args).
- `ThinkingRouter` + `NextStepPlanner` enrich → finalize.
- `StructuredOutputPipeline`(`JsonExtractor → AutoRepair → SchemaValidator`)을
  `ToolAgent` finalize에서 적용.

runner는 `CapturingToolRegistry`(`runners/common.py`)를 주입해 에이전트의 모든 도구
호출이 `TrialResult.tool_calls`에 기록되도록 한다. 토큰 수·턴 수는 `AgentResult.metadata`
(`exaone.observability.fields` 키)에서 직접 읽는다.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from eval.datasets.schema import EvalTask
from eval.metrics.types import TrialResult
from eval.runners.common import (
    DEFAULT_SYSTEM_PROMPT,
    build_capturing_registry,
    harness_agent_options,
    make_trial,
    retry_on_429,
    system_prompt_for,
    user_content_for,
)
from eval.runners.recovery_tracking import read_llm_recovery_stats, reset_llm_recovery_stats


def _is_429_runtime_error(exc: Exception) -> bool:
    """
    (en) `exaone.llm.ExaoneAPIClient` raises `RuntimeError("API 429 — ...")` on
    rate-limit. We match the prefix to add a fair backoff layer outside the
    client (same backoff the naive runner uses, see ``runners.common.retry_on_429``).

    (kr) `exaone.llm.ExaoneAPIClient`는 rate-limit 시 `RuntimeError("API 429 — ...")`를
    던진다. prefix로 매칭해 클라이언트 바깥에서 fair backoff 계층을 추가한다(naive runner와
    동일 backoff; ``runners.common.retry_on_429`` 참조).
    """
    return isinstance(exc, RuntimeError) and "API 429" in str(exc)

logger = logging.getLogger(__name__)


def _load_harness():
    """
    (en) Lazy import so this module loads in environments where `exaone/` is
    absent (e.g. when only running naive_runner tests).

    (kr) `exaone/` 미설치 환경(naive_runner 테스트만 돌릴 때 등)에서도 import 가능하도록
    lazy import.
    """
    from exaone.agents import AgentContext, ToolAgent
    from exaone.llm import ExaoneClient
    from exaone.observability import fields as obs_fields

    return AgentContext, ToolAgent, ExaoneClient, obs_fields


def make_exaone_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
):
    """
    (en) Build a production client from env defaults with eval-only M10 recovery counters.

    (kr) 환경변수 기본값으로 eval 전용 M10 recovery 카운터가 붙은 클라이언트를 구성한다.
    """
    from eval.runners.recovery_tracking import make_recovery_tracking_client

    return make_recovery_tracking_client(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )


class _UsageTrackingLLM:
    """
    (en) Transparent wrapper around any `ExaoneClient`-shaped object. Forwards
    `.chat(...)` while summing `resp.usage["prompt_tokens"]` / `["completion_tokens"]`
    across every router / enrich / finalize call. `LlmCallRecord` does not track
    tokens, so we collect them here instead.

    The wrapper preserves `.model`, `.DEFAULT_MODEL`, and `.chat_stream` so the
    harness can use it as a drop-in replacement.

    (kr) `ExaoneClient` 형태 객체를 투명하게 감싼다. `.chat(...)`을 그대로 위임하면서
    router/enrich/finalize 모든 호출의 `resp.usage["prompt_tokens"]`/`["completion_tokens"]`를
    합산한다. `LlmCallRecord`는 토큰을 추적하지 않으므로 여기서 직접 수집한다.

    `.model`, `.DEFAULT_MODEL`, `.chat_stream`을 보존해 하네스가 drop-in으로 사용할 수 있다.
    """

    def __init__(self, inner: Any):
        self._inner = inner
        self.input_tokens = 0
        self.output_tokens = 0
        self.call_count = 0
        self.model = getattr(inner, "model", None)
        self.DEFAULT_MODEL = getattr(inner, "DEFAULT_MODEL", self.model)

    def chat(self, messages, options=None):
        resp = retry_on_429(
            lambda: self._inner.chat(messages, options=options),
            is_429=_is_429_runtime_error,
        )
        usage = getattr(resp, "usage", None) or {}
        if isinstance(usage, dict):
            self.input_tokens += int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
            self.output_tokens += int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        self.call_count += 1
        return resp

    def chat_stream(self, messages, options=None):
        return self._inner.chat_stream(messages, options=options)


def _extract_turns(metadata: dict[str, Any], obs_fields, fallback_call_count: int) -> int:
    """
    (en) Prefer `TURNS_USED` when written, else count `LLM_CALLS` entries, else
    fall back to the raw wrapper call count.

    (kr) `TURNS_USED`가 있으면 우선 사용, 없으면 `LLM_CALLS` 항목 수, 그것도 없으면
    wrapper의 raw call count로 폴백.
    """
    if obs_fields.TURNS_USED in metadata:
        try:
            return int(metadata[obs_fields.TURNS_USED])
        except (TypeError, ValueError):
            pass
    calls = metadata.get(obs_fields.LLM_CALLS) or []
    if isinstance(calls, list) and calls:
        return len(calls)
    return fallback_call_count


def _normalize_structured(structured: Any, final_content: str) -> Any:
    """
    (en) The harness already runs `StructuredOutputPipeline` and stores the
    parsed payload on `AgentResult.structured`. If that is None but content
    looks like JSON, try a last-mile parse so M1 exact mode still works on
    naive vs harness comparison.

    (kr) 하네스는 이미 `StructuredOutputPipeline`을 실행해 결과를 `AgentResult.structured`에
    담는다. 그것이 None이면서 content가 JSON처럼 보이면 마지막에 한 번 더 파싱을 시도해
    naive vs 하네스 비교에서 M1 exact 모드가 일관되게 작동하도록 한다.
    """
    if structured is not None:
        return structured
    s = (final_content or "").strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def run_trial(
    task: EvalTask,
    *,
    llm: Any,
    trial_id: str | None = None,
    max_turns: int = 10,
    use_thinking_router: bool | None = None,
    use_next_step_planner: bool | None = None,
    system_prompt: str | None = None,
) -> TrialResult:
    """
    (en) Run one task through `ToolAgent.run()` and produce a `TrialResult`.

    Args:
        llm: any `ExaoneClient` (production `ExaoneAPIClient` or a test fake).
        max_turns: agent loop cap (harness default 10).
        use_thinking_router / use_next_step_planner: pass-through toggles —
          set to False to ablate one harness feature at a time.

    (kr) 한 태스크를 `ToolAgent.run()`으로 실행하고 `TrialResult`로 반환한다.

    인자:
        llm: 임의의 `ExaoneClient` (운영용 `ExaoneAPIClient` 또는 테스트 fake).
        max_turns: 에이전트 루프 상한(하네스 기본 10).
        use_thinking_router / use_next_step_planner: 전달 토글 — 하나씩 끄면 해당 기능
          ablation 가능.
    """
    AgentContext, ToolAgent, ExaoneClient, obs_fields = _load_harness()

    tid = trial_id or f"harness-{task.task_id}-{uuid.uuid4().hex[:6]}"
    registry, executor = build_capturing_registry(task.tools or [], task_id=task.task_id)
    tracked_llm = _UsageTrackingLLM(llm)
    reset_llm_recovery_stats(tracked_llm)

    agent_opts = harness_agent_options(task)
    resolved_router = (
        use_thinking_router
        if use_thinking_router is not None
        else agent_opts["use_thinking_router"]
    )
    resolved_planner = (
        use_next_step_planner
        if use_next_step_planner is not None
        else agent_opts["use_next_step_planner"]
    )

    agent = ToolAgent(
        tool_registry=registry,
        system_prompt=system_prompt or system_prompt_for(task, default=DEFAULT_SYSTEM_PROMPT),
        max_turns=max_turns,
        use_thinking_router=resolved_router,
        use_next_step_planner=resolved_planner,
    )

    t_start = time.monotonic()
    try:
        result = agent.run(
            AgentContext(query=user_content_for(task)),
            llm=tracked_llm,
        )
        error = result.error if not result.success else None
    except Exception as e:
        logger.exception("ToolAgent.run failed for task %s", task.task_id)
        total_latency_ms = (time.monotonic() - t_start) * 1000
        return make_trial(
            task=task,
            runner="harness",
            trial_id=tid,
            final_content="",
            final_structured=None,
            captured_calls=executor.calls,
            turns=tracked_llm.call_count,
            input_tokens=tracked_llm.input_tokens,
            output_tokens=tracked_llm.output_tokens,
            total_latency_ms=total_latency_ms,
            finished=False,
            error=f"ToolAgent.run raised: {e}",
        )

    total_latency_ms = (time.monotonic() - t_start) * 1000
    meta = dict(result.metadata or {})
    turns = _extract_turns(meta, obs_fields, fallback_call_count=tracked_llm.call_count)
    structured = _normalize_structured(result.structured, result.content or "")
    recovery = read_llm_recovery_stats(tracked_llm)

    return make_trial(
        task=task,
        runner="harness",
        trial_id=tid,
        final_content=result.content or "",
        final_structured=structured,
        captured_calls=executor.calls,
        turns=turns,
        input_tokens=tracked_llm.input_tokens,
        output_tokens=tracked_llm.output_tokens,
        total_latency_ms=total_latency_ms,
        finished=bool(result.success),
        error=error,
        metadata={
            "agent_metadata": meta,
            "reasoning_content": result.reasoning_content,
            "recovery": recovery.to_metadata(),
        },
    )


__all__ = ["run_trial", "make_exaone_client"]
