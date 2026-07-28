from __future__ import annotations

from eval.metrics import m9_faithfulness
from eval.metrics.m9_faithfulness import GroundingSpec, LengthRatioJudge
from eval.metrics.types import TrialResult


class TestLengthRatioJudgeStub:
    def test_fully_grounded(self):
        t = TrialResult(
            trial_id="x", task_id="t1", dataset="d", runner="harness",
            final_content="seoul is the capital",
        )
        judge = LengthRatioJudge()
        assert judge(trial=t, gold={"context": "Seoul is the capital city of Korea."}) == 1.0

    def test_zero_when_empty_answer(self):
        t = TrialResult(trial_id="x", task_id="t1", dataset="d", runner="harness")
        judge = LengthRatioJudge()
        assert judge(trial=t, gold={"context": "anything"}) == 0.0

    def test_partial_overlap(self):
        t = TrialResult(
            trial_id="x", task_id="t1", dataset="d", runner="harness",
            final_content="seoul tokyo",
        )
        judge = LengthRatioJudge()
        assert judge(trial=t, gold={"context": "Seoul is in Korea."}) == 0.5


class TestCompute:
    def test_clamps_judge_to_unit_range(self):
        t = TrialResult(trial_id="x", task_id="t1", dataset="d", runner="harness", final_content="hi")
        def naughty_judge(*, trial, gold):
            return 1.5
        s = m9_faithfulness.compute(
            [t], {"t1": GroundingSpec(context="hi there")}, judge=naughty_judge
        )
        assert s.metric_id == "M9"
        assert s.value == 1.0

    def test_skips_missing_grounding(self):
        t = TrialResult(trial_id="x", task_id="missing", dataset="d", runner="harness", final_content="hi")
        s = m9_faithfulness.compute([t], {}, judge=LengthRatioJudge())
        assert s.n == 0
