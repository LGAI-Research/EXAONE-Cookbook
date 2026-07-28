"""
(en) M8 — Redundancy Rate.

For each trial we count how many of its tool calls are duplicates of an earlier call
in the **same** trial. Two calls are duplicates iff they share the same canonical key
(`canonical_call_key(name, arguments)` — same rule as `ToolInvocationLedger`).

`Redundancy = #duplicate_calls / #total_calls`  (lower is better)

Aggregation modes:

- `micro`: pool all calls across trials, then divide (volume-weighted).
- `macro`: average per-trial ratio (trial-weighted; trials with 0 calls skipped).

Reference: Toolscore Redundancy (weight 0.10, inverted), sentinel LoopDetectionGuard
(hard loop vs semantic loop). We capture only **hard** loops here; semantic
near-duplicate detection is intentionally out of scope (requires embeddings).

(kr) M8 — Redundancy Rate.

trial별로 같은 trial 안에서 이전 호출과 중복인 도구 호출 개수를 센다. 동일성 기준은
canonical 키(`canonical_call_key(name, arguments)`)이며 `ToolInvocationLedger`와 동일 규칙이다.

`Redundancy = #duplicate_calls / #total_calls`  (작을수록 좋음)

집계 모드:

- `micro`: trial 전체 호출을 합쳐서 비율 계산(호출량 가중).
- `macro`: trial별 비율 평균(trial 가중, 호출 0건인 trial 제외).

참조: Toolscore Redundancy (가중치 0.10, inverted), sentinel LoopDetectionGuard
(hard loop vs semantic loop). 본 모듈은 **hard** loop만 탐지한다(의미적 유사 호출은
임베딩이 필요하므로 의도적으로 범위 외).
"""
from __future__ import annotations

from typing import Sequence

from eval.metrics._canonical import canonical_call_key
from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, TrialResult


def _count_duplicates(trial: TrialResult) -> tuple[int, int]:
    """
    (en) Returns (duplicate_calls, total_calls) for one trial.

    (kr) trial 한 건의 (중복 호출 수, 전체 호출 수).
    """
    seen: set[str] = set()
    dup = 0
    for tc in trial.tool_calls:
        key = canonical_call_key(tc.name, tc.arguments)
        if key in seen:
            dup += 1
        else:
            seen.add(key)
    return dup, len(trial.tool_calls)


def compute(trials: Sequence[TrialResult]) -> MetricSummary:
    """
    (en) Aggregate redundancy across trials. Reports both micro and macro views.

    (kr) trial 전체에 대한 redundancy 집계. micro와 macro 두 가지 시각을 모두 보고.
    """
    total_dup = 0
    total_calls = 0
    per_trial_ratios: list[float] = []
    for t in trials:
        d, n = _count_duplicates(t)
        total_dup += d
        total_calls += n
        if n > 0:
            per_trial_ratios.append(d / n)

    micro = (total_dup / total_calls) if total_calls > 0 else 0.0
    macro = mean(per_trial_ratios)
    lo, hi = bootstrap_ci(per_trial_ratios)
    return MetricSummary(
        metric_id="M8",
        name="Redundancy Rate",
        value=micro,
        n=total_calls,
        ci_low=lo,
        ci_high=hi,
        breakdown={
            "micro": micro,
            "macro": macro,
            "duplicate_calls_total": float(total_dup),
            "total_calls": float(total_calls),
            "trials_with_calls": float(len(per_trial_ratios)),
        },
        notes="value = micro (volume-weighted); macro in breakdown",
    )


__all__ = ["compute"]
