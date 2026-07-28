"""
(en) M2 — pass^k reliability.

`pass^k = (1/N) Σᵢ Πⱼ 1[rᵢⱼ = 1]`  (j = 1..k)

Unlike pass@k (which is "succeeds at least once across k tries"), pass^k requires that
**all** k independent trials of the same task succeed. The metric input is a per-task
list of binary success indicators; this module is decoupled from how success was scored
(typically reuses M1 score_trial_exact / judge to fill in the booleans).

Reference: τ-bench (Sierra/Princeton, Yao et al. 2024).

(kr) M2 — pass^k 재현 신뢰도.

`pass^k = (1/N) Σᵢ Πⱼ 1[rᵢⱼ = 1]`  (j = 1..k)

pass@k(k번 중 한 번이라도 성공)와 달리 pass^k는 같은 태스크의 k번 독립 trial이 **모두**
성공해야 한다. 입력은 태스크별 binary 성공 지시자 리스트이며, 어떻게 성공 여부를
산정했는지(보통 M1의 score_trial_exact / judge 결과 활용)와 분리되어 있다.

참조: τ-bench (Sierra/Princeton, Yao et al. 2024).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, TrialResult


@dataclass(frozen=True)
class PassKBreakdown:
    """
    (en) per-k value to support `pass^1, pass^2, pass^4, pass^8` panels.

    (kr) `pass^1, pass^2, pass^4, pass^8` 패널을 위한 k별 값.
    """

    k: int
    value: float
    n_tasks: int


def _task_success_lists(
    trials_by_task: Mapping[str, Sequence[TrialResult]],
    scorer,
    golds,
) -> dict[str, list[int]]:
    """
    (en) Apply `scorer(trial, gold)` -> {0, 1} for every trial; drop tasks without gold.

    (kr) 모든 trial에 `scorer(trial, gold)` -> {0, 1}을 적용. gold 없는 태스크는 제외.
    """
    out: dict[str, list[int]] = {}
    for task_id, trials in trials_by_task.items():
        g = golds.get(task_id)
        if g is None:
            continue
        out[task_id] = [1 if float(scorer(trial=t, gold=g)) >= 1.0 else 0 for t in trials]
    return out


def pass_k(success_lists: Mapping[str, Sequence[int]], k: int) -> float:
    """
    (en) `pass^k`. Tasks with fewer than k trials are skipped.

    (kr) `pass^k`. trial 수가 k 미만인 태스크는 제외한다.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    eligible = [s for s in success_lists.values() if len(s) >= k]
    if not eligible:
        return 0.0
    scored = [1 if all(s[:k]) else 0 for s in eligible]
    return mean(scored)


def compute(
    trials_by_task: Mapping[str, Sequence[TrialResult]],
    golds: Mapping[str, object],
    scorer,
    *,
    ks: Sequence[int] = (1, 2, 4, 8),
) -> MetricSummary:
    """
    (en) Compute pass^k for each k in `ks` and return a MetricSummary whose `value` is
    pass^max(k) (the strictest), with all values in `breakdown`.

    (kr) `ks`의 각 k에 대해 pass^k를 계산. `value`는 가장 엄격한 pass^max(k),
    나머지 값은 `breakdown`에 담는다.
    """
    success_lists = _task_success_lists(trials_by_task, scorer, golds)
    breakdown: dict[str, float] = {}
    per_task_for_ci: list[float] = []
    for k in ks:
        breakdown[f"pass_{k}"] = pass_k(success_lists, k)
    max_k = max(ks)
    eligible_for_max = [s for s in success_lists.values() if len(s) >= max_k]
    per_task_for_ci = [1.0 if all(s[:max_k]) else 0.0 for s in eligible_for_max]
    lo, hi = bootstrap_ci(per_task_for_ci)
    return MetricSummary(
        metric_id="M2",
        name=f"pass^k reliability (k={max_k})",
        value=breakdown[f"pass_{max_k}"],
        n=len(eligible_for_max),
        ci_low=lo,
        ci_high=hi,
        breakdown=breakdown,
        notes=f"ks={list(ks)}; n_tasks_total={len(success_lists)}",
    )


__all__ = ["PassKBreakdown", "pass_k", "compute"]
