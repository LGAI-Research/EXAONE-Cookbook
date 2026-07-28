from __future__ import annotations

from eval.metrics import m10_empty_recovery
from eval.metrics.types import TrialResult


class TestM10EmptyRecovery:
    def test_skips_trials_without_triggers(self):
        t = TrialResult(
            trial_id="x",
            task_id="t1",
            dataset="bfcl_v3.simple",
            runner="harness",
            metadata={"recovery": {"empty_triggers": 0, "recovery_successes": 0}},
        )
        assert m10_empty_recovery.trial_recovery_rate(t) is None
        summary = m10_empty_recovery.compute([t])
        assert summary.n == 0

    def test_harness_recovery_rate(self):
        t = TrialResult(
            trial_id="x",
            task_id="t1",
            dataset="bfcl_v3.simple",
            runner="harness",
            metadata={"recovery": {"empty_triggers": 2, "recovery_successes": 1}},
        )
        assert m10_empty_recovery.trial_recovery_rate(t) == 0.5

    def test_naive_zero_success_with_triggers(self):
        t = TrialResult(
            trial_id="x",
            task_id="t1",
            dataset="bfcl_v3.simple",
            runner="naive",
            metadata={"recovery": {"empty_triggers": 1, "recovery_successes": 0}},
        )
        summary = m10_empty_recovery.compute([t])
        assert summary.metric_id == "M10"
        assert summary.n == 1
        assert summary.value == 0.0
