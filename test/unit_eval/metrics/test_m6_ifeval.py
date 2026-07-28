from __future__ import annotations

from eval.datasets.schema import EvalTask
from eval.metrics import m6_ifeval
from eval.metrics.m6_ifeval import IFEvalSpec
from eval.metrics.types import TrialResult
from eval.pipeline import compute_metrics


def _no_comma_spec() -> IFEvalSpec:
    return IFEvalSpec(
        prompt="Write about databases.",
        instructions=[{"id": "punctuation:no_comma", "kwargs": {}}],
    )


class TestM6IFEvalScoring:
    def test_no_comma_strict_pass_and_fail(self):
        spec = _no_comma_spec()
        ok = TrialResult(
            trial_id="a",
            task_id="ifeval_1",
            dataset="ifeval",
            runner="harness",
            final_content="A clean sentence without punctuation issues.",
        )
        bad = TrialResult(
            trial_id="b",
            task_id="ifeval_1",
            dataset="ifeval",
            runner="naive",
            final_content="This has a comma, which violates the rule.",
        )
        assert m6_ifeval.score_trial(ok, spec) == (True, True)
        assert m6_ifeval.score_trial(bad, spec)[0] is False

    def test_loose_can_recover_leading_line(self):
        spec = _no_comma_spec()
        trial = TrialResult(
            trial_id="c",
            task_id="ifeval_1",
            dataset="ifeval",
            runner="harness",
            final_content="Sure, here is the answer.\nA clean sentence without issues.",
        )
        strict, loose = m6_ifeval.score_trial(trial, spec)
        assert strict is False
        assert loose is True

    def test_compute_summary(self):
        spec = _no_comma_spec()
        trials = [
            TrialResult(
                trial_id="a",
                task_id="ifeval_1",
                dataset="ifeval",
                runner="harness",
                final_content="Valid text only.",
            ),
            TrialResult(
                trial_id="b",
                task_id="ifeval_1",
                dataset="ifeval",
                runner="naive",
                final_content="Bad, comma.",
            ),
        ]
        summary = m6_ifeval.compute(trials, {"ifeval_1": spec})
        assert summary.metric_id == "M6"
        assert summary.n == 2
        assert summary.breakdown["mode"] == "ifeval"
        assert 0.0 <= summary.breakdown["strict"] <= 1.0


def test_pipeline_includes_m6_for_ifeval_tasks():
    task = EvalTask(
        task_id="ifeval_99",
        dataset="ifeval",
        category="verifiable_instructions",
        query="Say hello.",
        metadata={
            "ifeval_instructions": [{"id": "punctuation:no_comma", "kwargs": {}}],
        },
    )
    trials = [
        TrialResult(
            trial_id="t1",
            task_id=task.task_id,
            dataset=task.dataset,
            runner="harness",
            final_content="Hello world",
        )
    ]
    metrics = compute_metrics(trials, {task.task_id: trials}, [task], pass_k_trials=1)
    assert "M6" in metrics
    assert metrics["M6"]["breakdown"]["mode"] == "ifeval"
