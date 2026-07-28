"""
(en) M1 — Task Success Rate (TSR).

`TSR = (1/N) Σ 1[ŷᵢ ⊨ yᵢ]`

Two scoring backends are supported:

- `exact`: scalar / entity tasks; uses `_canonical.values_match` (BFCL-style normalization).
- `judge`: free-form answers; delegates to a `JudgeProtocol` callable injected by the runner
  (the metric module itself stays provider-agnostic; production wires `ExaoneAPIClient` or a
  separate judge model).

Reference: AgentBench Success Rate, AgencyBench Average Score, τ-bench reward r ∈ {0,1}.

(kr) M1 — Task Success Rate (TSR).

`TSR = (1/N) Σ 1[ŷᵢ ⊨ yᵢ]`

채점 백엔드 두 가지를 지원한다.

- `exact`: 스칼라/엔티티 태스크. `_canonical.values_match`(BFCL 정규화)를 사용.
- `judge`: 자유응답 태스크. 호출부가 주입하는 `JudgeProtocol` callable로 위임한다
  (metric 모듈은 provider 비의존을 유지; 운영은 `ExaoneAPIClient` 또는 별도 judge 모델을 연결).

참조: AgentBench Success Rate, AgencyBench Average Score, τ-bench reward r ∈ {0,1}.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from eval.metrics._canonical import values_match
from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.types import MetricSummary, TrialResult


class JudgeProtocol(Protocol):
    """
    (en) Callable used by M1 (free-form) and M9 (faithfulness).
    Returns a float in [0, 1] for a single (trial, gold) pair.

    (kr) M1(자유응답)·M9(faithfulness)에서 사용하는 callable.
    한 (trial, gold) 쌍에 대해 [0, 1] 범위의 float를 반환한다.
    """

    def __call__(self, *, trial: TrialResult, gold: Mapping[str, Any]) -> float: ...


@dataclass(frozen=True)
class TaskGold:
    """
    (en) Ground truth payload for one task. `answer` is used for exact mode; `rubric`
    is passed to the judge callable in judge mode (judge is responsible for parsing it).

    (kr) 한 태스크의 정답 페이로드. `answer`는 exact 모드, `rubric`은 judge 모드에서
    judge callable로 전달한다(rubric 파싱은 judge 책임).
    """

    task_id: str
    answer: Any = None
    rubric: str | None = None


def _final_payload(trial: TrialResult) -> Any:
    """
    (en) Prefer structured payload (post-pipeline) over raw content.

    (kr) 후처리된 structured payload가 있으면 우선 사용한다.
    """
    return trial.final_structured if trial.final_structured is not None else trial.final_content


def score_trial_exact(trial: TrialResult, gold: TaskGold) -> float:
    """
    (en) Returns 1.0 if normalized predicted answer matches `gold.answer`, else 0.0.
    When `gold.answer` is a dict, supports key-wise BFCL-style matching.

    (kr) 정규화된 예측 답이 `gold.answer`와 일치하면 1.0, 아니면 0.0.
    `gold.answer`가 dict이면 키 단위 BFCL 스타일 비교를 지원한다.
    """
    if gold.answer is None:
        return 0.0
    pred = _final_payload(trial)
    return 1.0 if values_match(pred, gold.answer) else 0.0


def compute(
    trials: Sequence[TrialResult],
    golds: Mapping[str, TaskGold],
    *,
    mode: str = "exact",
    judge: JudgeProtocol | None = None,
) -> MetricSummary:
    """
    (en) Compute TSR across `trials`. `golds` is keyed by task_id.

    Args:
        mode: "exact" or "judge".
        judge: required when mode == "judge".

    (kr) `trials` 전체에 대한 TSR을 계산한다. `golds`는 task_id 키.

    Args:
        mode: "exact" 또는 "judge".
        judge: mode == "judge"일 때 필수.
    """
    if mode == "judge" and judge is None:
        raise ValueError("M1 judge mode requires a JudgeProtocol callable")

    scores: list[float] = []
    skipped: list[str] = []
    for t in trials:
        g = golds.get(t.task_id)
        if g is None:
            skipped.append(t.task_id)
            continue
        if mode == "exact":
            scores.append(score_trial_exact(t, g))
        else:
            assert judge is not None
            scores.append(
                float(judge(trial=t, gold={"answer": g.answer, "rubric": g.rubric}))
            )

    value = mean(scores)
    lo, hi = bootstrap_ci(scores)
    return MetricSummary(
        metric_id="M1",
        name="Task Success Rate",
        value=value,
        n=len(scores),
        ci_low=lo,
        ci_high=hi,
        breakdown={
            "skipped_no_gold": float(len(skipped)),
        },
        notes=f"mode={mode}",
    )


__all__ = [
    "JudgeProtocol",
    "TaskGold",
    "score_trial_exact",
    "compute",
]
