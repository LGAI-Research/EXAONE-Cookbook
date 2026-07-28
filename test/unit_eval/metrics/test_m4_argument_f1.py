from __future__ import annotations

from eval.metrics import m4_argument_f1
from eval.metrics.m4_argument_f1 import score_trial
from eval.metrics.types import ToolCallRecord


class TestScoreTrial:
    def test_perfect_match(self, trial_ok_simple):
        gold = [ToolCallRecord(name="rag.retrieve", arguments={"q": "seoul population"})]
        assert score_trial(trial_ok_simple, gold) == 1.0

    def test_wrong_value_drops_to_zero(self, trial_wrong_args):
        gold = [ToolCallRecord(name="rag.retrieve", arguments={"q": "Seoul population"})]
        assert score_trial(trial_wrong_args, gold) == 0.0

    def test_missing_predicted_call(self, trial_ok_simple):
        # gold expects 2 calls, trial only made 1 → partial credit
        gold = [
            ToolCallRecord(name="rag.retrieve", arguments={"q": "seoul population"}),
            ToolCallRecord(name="weather", arguments={"city": "seoul"}),
        ]
        score = score_trial(trial_ok_simple, gold)
        assert 0 < score < 1

    def test_both_empty_is_one(self):
        from eval.metrics.types import TrialResult

        t = TrialResult(trial_id="x", task_id="x", dataset="d", runner="harness", tool_calls=[])
        assert score_trial(t, []) == 1.0


class TestCompute:
    def test_aggregate(self, trial_ok_simple, trial_wrong_args):
        gold = {
            "bfcl.simple.001": [
                ToolCallRecord(name="rag.retrieve", arguments={"q": "seoul population"})
            ]
        }
        s = m4_argument_f1.compute([trial_ok_simple, trial_wrong_args], gold)
        assert s.metric_id == "M4"
        assert s.n == 2
        assert s.value == 0.5  # one perfect, one zero
