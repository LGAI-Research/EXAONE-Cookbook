"""
(en) M7 — Trajectory Efficiency (step / token efficiency).

Single-number summaries (intended for Pareto plots, not for ranking on their own):

- `StepEff  = TSR / mean(turns_used)`
- `TokenEff = TSR / (mean(total_tokens) / 1000)`

Per-trial means are reported in `breakdown` so the caller can render distributions
(p50 / p95) or a Pareto scatter (x = mean tokens, y = TSR).

Reference: AgencyBench Attempt Efficiency / Token Efficiency (Fig. 4).

(kr) M7 — Trajectory Efficiency (step / token 효율).

요약 단일값(Pareto 산점도 보조용; 단독 랭킹용은 아님):

- `StepEff  = TSR / mean(turns_used)`
- `TokenEff = TSR / (mean(total_tokens) / 1000)`

trial 평균은 `breakdown`에 함께 담아 호출부가 분포(p50/p95)나 Pareto 산점도(x = 평균
토큰, y = TSR)를 그릴 수 있게 한다.

참조: AgencyBench Attempt Efficiency / Token Efficiency (Fig. 4).
"""
from __future__ import annotations

import statistics
from typing import Sequence

from eval.metrics._stats import mean
from eval.metrics.types import MetricSummary, TrialResult


def _percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((pct / 100.0) * (len(s) - 1)))))
    return float(s[k])


def compute(
    trials: Sequence[TrialResult],
    *,
    tsr: float,
) -> MetricSummary:
    """
    (en) `tsr` is the M1 value for the same trial set (passed in by the caller to
    keep M7 dependency-free from M1).

    (kr) `tsr`은 같은 trial 집합의 M1 값(호출부가 전달; M7이 M1에 의존하지 않게).
    """
    turns = [float(t.turns) for t in trials]
    tokens = [float(t.total_tokens) for t in trials]

    mean_turns = mean(turns)
    mean_tokens = mean(tokens)
    step_eff = (tsr / mean_turns) if mean_turns > 0 else 0.0
    token_eff = (tsr / (mean_tokens / 1000.0)) if mean_tokens > 0 else 0.0

    return MetricSummary(
        metric_id="M7",
        name="Trajectory Efficiency",
        value=token_eff,
        n=len(trials),
        ci_low=None,
        ci_high=None,
        breakdown={
            "tsr": tsr,
            "mean_turns": mean_turns,
            "p50_turns": _percentile(turns, 50),
            "p95_turns": _percentile(turns, 95),
            "mean_tokens": mean_tokens,
            "p50_tokens": _percentile(tokens, 50),
            "p95_tokens": _percentile(tokens, 95),
            "step_eff": step_eff,
            "token_eff": token_eff,
        },
        notes="value = token_eff; use breakdown for Pareto plot",
    )


__all__ = ["compute"]
