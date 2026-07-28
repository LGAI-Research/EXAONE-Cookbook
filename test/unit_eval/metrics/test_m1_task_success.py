from __future__ import annotations

from eval.metrics import m1_task_success
from eval.metrics.m1_task_success import TaskGold


class TestExactMode:
    def test_exact_match_on_structured(self, trial_ok_simple):
        golds = {trial_ok_simple.task_id: TaskGold(task_id=trial_ok_simple.task_id, answer={"city": "Seoul"})}
        s = m1_task_success.compute([trial_ok_simple], golds, mode="exact")
        assert s.metric_id == "M1"
        assert s.value == 1.0
        assert s.n == 1

    def test_wrong_answer_returns_zero(self, trial_wrong_args):
        golds = {trial_wrong_args.task_id: TaskGold(task_id=trial_wrong_args.task_id, answer="Seoul")}
        s = m1_task_success.compute([trial_wrong_args], golds, mode="exact")
        assert s.value == 0.0

    def test_skips_when_no_gold(self, trial_ok_simple):
        s = m1_task_success.compute([trial_ok_simple], golds={}, mode="exact")
        assert s.value == 0.0
        assert s.n == 0
        assert s.breakdown["skipped_no_gold"] == 1.0


class TestJudgeMode:
    def test_requires_judge_callable(self, trial_ok_simple):
        import pytest

        with pytest.raises(ValueError):
            m1_task_success.compute([trial_ok_simple], {}, mode="judge")

    def test_judge_score_propagates(self, trial_ok_simple):
        def judge(*, trial, gold):
            return 0.7

        golds = {trial_ok_simple.task_id: TaskGold(task_id=trial_ok_simple.task_id, rubric="any")}
        s = m1_task_success.compute([trial_ok_simple], golds, mode="judge", judge=judge)
        assert s.value == 0.7
