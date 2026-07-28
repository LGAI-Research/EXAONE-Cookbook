from __future__ import annotations

from eval.metrics import m5_abstention


class TestAbstention:
    def test_abstain_counts_as_one(self, trial_irrelevance_abstain):
        s = m5_abstention.compute(
            [trial_irrelevance_abstain],
            {trial_irrelevance_abstain.task_id: True},
        )
        assert s.metric_id == "M5"
        assert s.value == 1.0
        assert s.breakdown["hallucinated_calls_total"] == 0.0

    def test_hallucinated_call_counts_as_zero(self, trial_irrelevance_hallucinate):
        s = m5_abstention.compute(
            [trial_irrelevance_hallucinate],
            {trial_irrelevance_hallucinate.task_id: True},
        )
        assert s.value == 0.0
        assert s.breakdown["hallucinated_calls_total"] == 1.0

    def test_skips_tasks_not_marked_irrelevance(self, trial_ok_simple):
        s = m5_abstention.compute([trial_ok_simple], {trial_ok_simple.task_id: False})
        assert s.n == 0

    def test_mixed_batch(self, trial_irrelevance_abstain, trial_irrelevance_hallucinate):
        s = m5_abstention.compute(
            [trial_irrelevance_abstain, trial_irrelevance_hallucinate],
            {
                trial_irrelevance_abstain.task_id: True,
                trial_irrelevance_hallucinate.task_id: True,
            },
        )
        assert s.value == 0.5
        assert s.n == 2
