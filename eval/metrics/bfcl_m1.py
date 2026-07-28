"""
(en) M1/M2 helpers for BFCL tool tasks — population scope and OSS breakdown fields.

(kr) BFCL tool task용 M1/M2 helper — population 범위 및 OSS breakdown 필드.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from eval.datasets.schema import EvalTask
from eval.judges.bfcl_any_of import BFCLAnyOfJudge
from eval.metrics.types import TrialResult

BFCL_M1_DATASETS: frozenset[str] = frozenset(
    {
        "bfcl_v3.simple",
        "bfcl_v3.multiple",
        "bfcl_v3.parallel",
    }
)


def bfcl_m1_task_ids(tasks: Sequence[EvalTask]) -> frozenset[str]:
    """
    (en) Task ids that participate in M1/M2 when BFCL ground truth is present
    and the dataset is simple/multiple/parallel (excludes IFEval/HaluBench/irrelevance).

    (kr) BFCL ground truth가 있고 simple/multiple/parallel dataset인 M1/M2 집계 task id.
    """
    return frozenset(
        t.task_id
        for t in tasks
        if t.metadata.get("bfcl_ground_truth") and t.dataset in BFCL_M1_DATASETS
    )


def filter_bfcl_m1_trials(
    trials: Sequence[TrialResult],
    bfcl_task_ids: frozenset[str],
) -> list[TrialResult]:
    """
    (en) Keep only trials whose task_id is in the BFCL M1 population.

    (kr) BFCL M1 population에 해당하는 trial만 남긴다.
    """
    return [t for t in trials if t.task_id in bfcl_task_ids]


def filter_bfcl_m1_grouped(
    grouped: Mapping[str, Sequence[TrialResult]],
    bfcl_task_ids: frozenset[str],
) -> dict[str, list[TrialResult]]:
    """
    (en) Subset ``grouped`` to BFCL M1 task ids for pass^k.

    (kr) pass^k용 ``grouped``를 BFCL M1 task id만 남기도록 부분집합.
    """
    return {
        task_id: list(trials)
        for task_id, trials in grouped.items()
        if task_id in bfcl_task_ids
    }


def score_bfcl_trial(trial: TrialResult, bfcl_gold_metadata: Mapping[str, dict[str, Any]]) -> float:
    """
    (en) BFCL any-of score for one trial (0.0 or 1.0).

    (kr) trial 한 건의 BFCL any-of 점수(0.0 또는 1.0).
    """
    judge = BFCLAnyOfJudge()
    meta = bfcl_gold_metadata.get(trial.task_id) or {}
    return float(judge(trial=trial, gold=meta))


def build_bfcl_m1_breakdown(
    trials: Sequence[TrialResult],
    tasks_by_id: Mapping[str, EvalTask],
    bfcl_gold_metadata: Mapping[str, dict[str, Any]],
) -> dict[str, float]:
    """
    (en) OSS breakdown: per-dataset mean scores and harness failure mode counts.

    (kr) OSS breakdown: dataset별 평균 점수 및 harness 실패 모드 건수.
    """
    out: dict[str, float] = {
        "n_tasks": float(len(bfcl_gold_metadata)),
        "n_trials": float(len(trials)),
    }

    by_dataset: dict[str, list[float]] = defaultdict(list)
    no_tool_calls = 0.0
    wrong_tool_or_args = 0.0

    for trial in trials:
        if trial.task_id not in bfcl_gold_metadata:
            continue
        score = score_bfcl_trial(trial, bfcl_gold_metadata)
        task = tasks_by_id.get(trial.task_id)
        ds = task.dataset if task else "unknown"
        by_dataset[ds].append(score)
        if score >= 1.0:
            continue
        if trial.runner == "harness":
            if not trial.tool_calls:
                no_tool_calls += 1.0
            else:
                wrong_tool_or_args += 1.0

    for ds, scores in by_dataset.items():
        safe = ds.replace(".", "_")
        out[f"mean_{safe}"] = sum(scores) / len(scores) if scores else 0.0
        out[f"n_trials_{safe}"] = float(len(scores))

    out["harness_fail_no_tool_calls"] = no_tool_calls
    out["harness_fail_wrong_tool_or_args"] = wrong_tool_or_args
    return out


def population_note(*, n_tasks: int, n_trials: int) -> str:
    """
    (en) Human-readable M1/M2 scope note for MetricSummary.notes.

    (kr) MetricSummary.notes용 M1/M2 scope 설명.
    """
    ds_list = "|".join(sorted(BFCL_M1_DATASETS))
    return (
        f"population={ds_list}; n_tasks={n_tasks}; n_trials={n_trials}; "
        "judge=bfcl_any_of"
    )


__all__ = [
    "BFCL_M1_DATASETS",
    "bfcl_m1_task_ids",
    "filter_bfcl_m1_trials",
    "filter_bfcl_m1_grouped",
    "score_bfcl_trial",
    "build_bfcl_m1_breakdown",
    "population_note",
]
