from __future__ import annotations

from eval.datasets.schema import EvalTask
from eval.judges.context_overlap import ContextTokenOverlapJudge
from eval.metrics.types import ToolCallRecord, TrialResult
from eval.pipeline import compute_metrics


def _halubench_task() -> EvalTask:
    return EvalTask(
        task_id="hb-1",
        dataset="halubench",
        category="drop",
        query="What is the capital?",
        grounding_context="Seoul is the capital city of Korea.",
        expected_answer={"label": "PASS"},
    )


def test_compute_metrics_includes_m9_for_grounding_tasks():
    task = _halubench_task()
    trials = [
        TrialResult(
            trial_id="h-1",
            task_id=task.task_id,
            dataset=task.dataset,
            runner="harness",
            final_content="Seoul is the capital city of Korea.",
        )
    ]
    metrics = compute_metrics(trials, {task.task_id: trials}, [task], pass_k_trials=1)
    assert "M9" in metrics
    assert metrics["M9"]["metric_id"] == "M9"
    judge = ContextTokenOverlapJudge()
    assert judge(trial=trials[0], gold={"context": task.grounding_context}) == 1.0


def test_compute_metrics_m9_scores_harness_json_answer_not_wrapper():
    task = _halubench_task()
    trials = [
        TrialResult(
            trial_id="h-1",
            task_id=task.task_id,
            dataset=task.dataset,
            runner="harness",
            final_content='{"answer": "Seoul is the capital city of Korea.", "confidence": "high", "sources": []}',
            final_structured={
                "answer": "Seoul is the capital city of Korea.",
                "confidence": "high",
                "sources": [],
            },
        )
    ]
    metrics = compute_metrics(trials, {task.task_id: trials}, [task], pass_k_trials=1)
    assert metrics["M9"]["value"] == 1.0


def test_compute_metrics_includes_m10_when_recovery_triggers_present():
    task = EvalTask(
        task_id="bfcl.simple.001",
        dataset="bfcl_v3.simple",
        category="simple",
        query="hi",
    )
    trials = [
        TrialResult(
            trial_id="h-1",
            task_id=task.task_id,
            dataset=task.dataset,
            runner="harness",
            metadata={"recovery": {"empty_triggers": 1, "recovery_successes": 1}},
        ),
        TrialResult(
            trial_id="n-1",
            task_id=task.task_id,
            dataset=task.dataset,
            runner="naive",
            metadata={"recovery": {"empty_triggers": 1, "recovery_successes": 0}},
        ),
    ]
    metrics = compute_metrics(trials, {task.task_id: trials}, [task], pass_k_trials=1)
    assert "M10" in metrics
    assert metrics["M10"]["value"] == 0.5


def test_compute_metrics_omits_m10_without_triggers():
    task = EvalTask(
        task_id="bfcl.simple.002",
        dataset="bfcl_v3.simple",
        category="simple",
        query="hi",
    )
    trials = [
        TrialResult(
            trial_id="h-1",
            task_id=task.task_id,
            dataset=task.dataset,
            runner="harness",
            metadata={"recovery": {"empty_triggers": 0, "recovery_successes": 0}},
        )
    ]
    metrics = compute_metrics(trials, {task.task_id: trials}, [task], pass_k_trials=1)
    assert "M10" not in metrics


def test_compute_metrics_m1_excludes_ifeval_when_bfcl_present():
    bfcl_task = EvalTask(
        task_id="bfcl.simple.001",
        dataset="bfcl_v3.simple",
        category="simple",
        query="call tool",
        metadata={
            "bfcl_ground_truth": [
                {"search": {"q": ["exaone"]}},
            ]
        },
    )
    ifeval_task = _halubench_task()
    bfcl_trials = [
        TrialResult(
            trial_id="b-1",
            task_id=bfcl_task.task_id,
            dataset=bfcl_task.dataset,
            runner="harness",
            tool_calls=[ToolCallRecord(name="search", arguments={"q": "exaone"})],
        ),
        TrialResult(
            trial_id="b-2",
            task_id=bfcl_task.task_id,
            dataset=bfcl_task.dataset,
            runner="harness",
            tool_calls=[ToolCallRecord(name="search", arguments={"q": "wrong"})],
        ),
    ]
    ifeval_trials = [
        TrialResult(
            trial_id="i-1",
            task_id=ifeval_task.task_id,
            dataset=ifeval_task.dataset,
            runner="harness",
            final_content="Seoul is the capital city of Korea.",
        ),
    ]
    tasks = [bfcl_task, ifeval_task]
    trials = bfcl_trials + ifeval_trials
    grouped = {
        bfcl_task.task_id: bfcl_trials,
        ifeval_task.task_id: ifeval_trials,
    }
    metrics = compute_metrics(trials, grouped, tasks, pass_k_trials=2)
    assert metrics["M1"]["value"] == 0.5
    assert metrics["M1"]["n"] == 2
    assert "population=bfcl_v3.multiple|bfcl_v3.parallel|bfcl_v3.simple" in metrics["M1"]["notes"]

