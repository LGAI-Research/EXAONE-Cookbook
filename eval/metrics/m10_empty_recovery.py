"""
(en) M10 — Empty-response Recovery Score.

For each trial, read ``metadata["recovery"]`` populated by eval runners:

- ``empty_triggers``: LLM responses that needed content recovery (empty or reasoning-only).
- ``recovery_successes``: how many of those triggers were recovered (harness retry path).

Score a trial with triggers as ``recovery_successes / empty_triggers`` (clamped to [0, 1]).
Trials with zero triggers are skipped. Naive baseline increments triggers but not successes.

Reference: ``exaone.llm.response_quality`` + ``ExaoneAPIClient.chat`` retry path.

(kr) M10 — Empty-response Recovery Score.

각 trial의 ``metadata["recovery"]``(eval runner가 채움)를 읽는다.

- ``empty_triggers``: content 복구가 필요했던 LLM 응답(빈 content 또는 reasoning-only) 횟수.
- ``recovery_successes``: 그중 복구에 성공한 횟수(하네스 retry 경로).

trigger가 있는 trial은 ``recovery_successes / empty_triggers``([0, 1] clamp)로 점수화한다.
trigger가 0인 trial은 제외. naive baseline은 trigger만 증가하고 success는 0.

참조: ``exaone.llm.response_quality`` + ``ExaoneAPIClient.chat`` retry 경로.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, TrialResult


def _recovery_payload(trial: TrialResult) -> Mapping[str, Any]:
    raw = trial.metadata.get("recovery")
    return raw if isinstance(raw, Mapping) else {}


def trial_recovery_rate(trial: TrialResult) -> float | None:
    """
    (en) Per-trial recovery rate, or None when no empty/reasoning-only trigger occurred.

    (kr) trial별 recovery rate. trigger가 없으면 None.
    """
    rec = _recovery_payload(trial)
    triggers = int(rec.get("empty_triggers") or 0)
    if triggers <= 0:
        return None
    successes = int(rec.get("recovery_successes") or 0)
    return max(0.0, min(1.0, successes / triggers))


def compute(trials: Sequence[TrialResult]) -> MetricSummary:
    """
    (en) Mean recovery rate over trials that had at least one empty/reasoning-only trigger.

    (kr) empty/reasoning-only trigger가 1회 이상인 trial에 대해 평균 recovery rate.
    """
    scores: list[float] = []
    total_triggers = 0
    total_successes = 0
    for t in trials:
        rec = _recovery_payload(t)
        triggers = int(rec.get("empty_triggers") or 0)
        successes = int(rec.get("recovery_successes") or 0)
        total_triggers += triggers
        total_successes += successes
        rate = trial_recovery_rate(t)
        if rate is not None:
            scores.append(rate)

    value = mean(scores)
    lo, hi = bootstrap_ci(scores)
    return MetricSummary(
        metric_id="M10",
        name="Empty-response Recovery Score",
        value=value,
        n=len(scores),
        ci_low=lo,
        ci_high=hi,
        breakdown={
            "empty_triggers_total": float(total_triggers),
            "recovery_successes_total": float(total_successes),
            "micro_recovery_rate": (
                max(0.0, min(1.0, total_successes / total_triggers))
                if total_triggers > 0
                else 0.0
            ),
        },
        notes="trials with zero triggers are excluded; naive has no HTTP-layer retry",
    )


__all__ = ["trial_recovery_rate", "compute"]
