"""
(en) M9 — Faithfulness / Groundedness.

For each trial we ask a `JudgeProtocol` callable whether the final answer is fully
entailed by the grounding context (tool results / retrieval passages). The judge is
expected to return a float in [0, 1] (RAGAS-style faithfulness ratio: fraction of
claims supported by context).

This module deliberately does NOT include a default judge implementation — choice of
judge model (`ExaoneAPIClient`, a separate evaluator LM, or a deterministic NLI model)
is a runner-level decision. A stub `LengthRatioJudge` is provided only for unit tests.

Reference: RAGAS faithfulness, HaluBench / Lynx (reference-free).

(kr) M9 — Faithfulness / Groundedness.

trial별로 `JudgeProtocol` callable에 최종 답안이 grounding 컨텍스트(도구 결과/검색 결과)에
의해 entailment 되는지 평가를 요청한다. judge는 [0, 1] 범위의 float를 반환해야 한다
(RAGAS 스타일: 컨텍스트로 뒷받침되는 주장 비율).

기본 judge 구현은 의도적으로 제공하지 않는다(판단 모델 선택 — `ExaoneAPIClient`, 별도
evaluator LM, 결정론적 NLI 모델 등 — 은 runner 레벨 결정). 단위 테스트용으로
`LengthRatioJudge` 스텁만 제공한다.

참조: RAGAS faithfulness, HaluBench / Lynx (reference-free).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from eval.judges.context_overlap import faithfulness_answer_text
from eval.metrics._stats import bootstrap_ci, mean
from eval.metrics.m1_task_success import JudgeProtocol
from eval.metrics.types import MetricSummary, TrialResult


@dataclass(frozen=True)
class GroundingSpec:
    """
    (en) Per-task grounding context. `context` is the joined passage / tool-result text
    against which the final answer is judged.

    (kr) 태스크별 grounding 컨텍스트. `context`는 답변 판단의 기준이 되는 본문/도구 결과.
    """

    context: str
    expected_answer: Any = None


class LengthRatioJudge:
    """
    (en) **Test-only** stub. Returns the fraction of trial.final_content tokens that
    also appear in the context — never use in production.

    (kr) **테스트 전용** 스텁. trial.final_content 토큰 중 context에 등장하는 비율을
    반환 — 운영에서는 절대 사용 금지.
    """

    def __call__(self, *, trial: TrialResult, gold: Mapping[str, Any]) -> float:
        ctx = str(gold.get("context", "")).lower()
        ans = faithfulness_answer_text(trial).lower()
        toks = [t for t in ans.split() if t]
        if not toks:
            return 0.0
        hit = sum(1 for t in toks if t in ctx)
        return hit / len(toks)


def compute(
    trials: Sequence[TrialResult],
    specs_by_task: Mapping[str, GroundingSpec],
    judge: JudgeProtocol,
) -> MetricSummary:
    """
    (en) Aggregate faithfulness via the provided judge.

    (kr) judge를 사용해 faithfulness를 집계.
    """
    scores: list[float] = []
    for t in trials:
        spec = specs_by_task.get(t.task_id)
        if spec is None:
            continue
        s = float(
            judge(
                trial=t,
                gold={"context": spec.context, "expected_answer": spec.expected_answer},
            )
        )
        scores.append(max(0.0, min(1.0, s)))

    value = mean(scores)
    lo, hi = bootstrap_ci(scores)
    return MetricSummary(
        metric_id="M9",
        name="Faithfulness / Groundedness",
        value=value,
        n=len(scores),
        ci_low=lo,
        ci_high=hi,
        breakdown={},
        notes="judge must return float in [0,1]; clamped",
    )


__all__ = ["GroundingSpec", "LengthRatioJudge", "compute"]
