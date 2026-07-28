from __future__ import annotations

from eval.metrics import m2_pass_k
from eval.metrics.types import TrialResult


def _trial(task_id: str, content: str, idx: int) -> TrialResult:
    return TrialResult(
        trial_id=f"{task_id}#{idx}",
        task_id=task_id,
        dataset="dummy",
        runner="harness",
        final_content=content,
    )


class TestPassKPureFunction:
    def test_all_succeed(self):
        sl = {"a": [1, 1, 1, 1]}
        assert m2_pass_k.pass_k(sl, k=4) == 1.0

    def test_one_failure_drops_to_zero(self):
        sl = {"a": [1, 1, 0, 1]}
        assert m2_pass_k.pass_k(sl, k=4) == 0.0
        # but pass^2 still passes (first two were 1)
        assert m2_pass_k.pass_k(sl, k=2) == 1.0

    def test_skips_short_trials(self):
        sl = {"a": [1, 1, 1, 1], "b": [1, 1]}  # b has only 2 trials
        assert m2_pass_k.pass_k(sl, k=4) == 1.0  # only "a" eligible


class TestPassKCompute:
    def test_full_pipeline(self):
        # task "X" succeeds in 3/4 trials, task "Y" succeeds in 4/4
        trials_by_task = {
            "X": [_trial("X", "ok", i) for i in range(4)],
            "Y": [_trial("Y", "ok", i) for i in range(4)],
        }
        gold_lookup = {"X": "ok", "Y": "ok"}
        # judge: succeed if final_content == gold
        flip = {0: False}

        def scorer(*, trial, gold):
            if trial.task_id == "X" and trial.trial_id.endswith("#2"):
                return 0.0
            return 1.0 if trial.final_content == gold else 0.0

        summary = m2_pass_k.compute(trials_by_task, gold_lookup, scorer, ks=(1, 2, 4))
        assert summary.metric_id == "M2"
        assert summary.breakdown["pass_1"] == 1.0  # both first trials pass
        assert summary.breakdown["pass_2"] == 1.0  # both first-2 pass
        assert summary.breakdown["pass_4"] == 0.5  # X drops, Y holds
        assert summary.value == 0.5  # max k
