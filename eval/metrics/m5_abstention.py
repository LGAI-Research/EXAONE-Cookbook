"""
(en) M5 — Irrelevance / Abstention Rate.

For tasks marked `expected_no_tools = True` (BFCL v3 irrelevance / live_irrelevance),
the agent should output a non-function-call response. We score 1.0 iff the trial's
`tool_calls` is empty.

`Abstain = #{tool_calls = ∅ | gold = ∅} / #{gold = ∅}`

Reference: BFCL v3 Irrelevance Detection (875 cases).

(kr) M5 — Irrelevance / Abstention Rate.

`expected_no_tools = True`인 태스크(BFCL v3 irrelevance / live_irrelevance)는 모델이
함수 호출 없이 응답해야 한다. trial의 `tool_calls`가 비어 있으면 1.0.

`Abstain = #{tool_calls = ∅ | gold = ∅} / #{gold = ∅}`

참조: BFCL v3 Irrelevance Detection (875건).
"""
from __future__ import annotations

from typing import Mapping, Sequence

from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, TrialResult


def is_abstention(trial: TrialResult) -> bool:
    """
    (en) True iff no tool calls were issued in this trial.

    (kr) trial에서 도구 호출이 0건이면 True.
    """
    return len(trial.tool_calls) == 0


def compute(
    trials: Sequence[TrialResult],
    expected_no_tools_by_task: Mapping[str, bool],
) -> MetricSummary:
    """
    (en) Aggregate abstention over tasks where gold expects no tool call.
    Tasks not in `expected_no_tools_by_task` (or with value False) are skipped.

    (kr) 정답이 "도구 호출 없음"인 태스크에 대해서만 abstention을 집계한다.
    `expected_no_tools_by_task`에 없거나 False인 태스크는 제외.
    """
    scores: list[float] = []
    hallucinated_calls = 0
    for t in trials:
        if not expected_no_tools_by_task.get(t.task_id, False):
            continue
        if is_abstention(t):
            scores.append(1.0)
        else:
            scores.append(0.0)
            hallucinated_calls += len(t.tool_calls)

    value = mean(scores)
    lo, hi = bootstrap_ci(scores)
    return MetricSummary(
        metric_id="M5",
        name="Irrelevance / Abstention Rate",
        value=value,
        n=len(scores),
        ci_low=lo,
        ci_high=hi,
        breakdown={
            "hallucinated_calls_total": float(hallucinated_calls),
        },
        notes="evaluates only tasks with expected_no_tools=True",
    )


__all__ = ["is_abstention", "compute"]
