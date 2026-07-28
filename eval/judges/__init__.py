"""
(en) Judges used by M1 (Task Success) and M9 (Faithfulness) — kept separate from
the metric modules so swapping the judge model never requires touching M1/M9
maths. Each judge follows `eval.metrics.m1_task_success.JudgeProtocol`:

    judge(trial=TrialResult, gold=Mapping[str, Any]) -> float in [0, 1]

(kr) M1 (Task Success)·M9 (Faithfulness)에서 사용하는 judge들. metric 모듈과 분리해
judge 모델을 교체해도 M1/M9 수식에 손대지 않도록 한다. 모든 judge는
`eval.metrics.m1_task_success.JudgeProtocol`를 따른다:

    judge(trial=TrialResult, gold=Mapping[str, Any]) -> float in [0, 1]
"""
from __future__ import annotations

from eval.judges.bfcl_any_of import BFCLAnyOfJudge
from eval.judges.context_overlap import ContextTokenOverlapJudge

__all__ = ["BFCLAnyOfJudge", "ContextTokenOverlapJudge"]
