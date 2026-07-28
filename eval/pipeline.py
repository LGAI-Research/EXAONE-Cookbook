"""
(en) Evaluation pipeline: load tasks, run runners, compute M1–M10, build a
`ComparisonReport`.

(kr) 평가 파이프라인: task 로드, runner 실행, M1–M10 계산, `ComparisonReport` 조립.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from eval._env import slug_endpoint
from eval.datasets.schema import EvalTask
from eval.metrics.types import TrialResult
from eval.report import (
    ComparisonReport,
    RunnerSummary,
    compute_deltas,
    enrich_metrics,
    timestamp_from_run_id,
    utc_timestamp,
)

logger = logging.getLogger("eval.pipeline")


@dataclass(frozen=True)
class RunConfig:
    """
    (en) Resolved CLI/runtime options for one comparison run.

    (kr) 한 번의 비교 실행에 대한 CLI/런타임 옵션.
    """

    datasets: tuple[str, ...]
    limit: int | None
    pass_k_trials: int
    runners: tuple[str, ...]
    naive_max_turns: int
    harness_max_turns: int
    sleep_between_trials: float
    checkpoint: bool = False
    checkpoint_dir: Path | None = None
    resume_run_id: str | None = None


def gather_tasks(datasets: Sequence[str], limit: int | None) -> list[EvalTask]:
    """
    (en) Concatenate tasks from each dataset name.

    (kr) dataset 이름별 task를 이어 붙여 반환.
    """
    from eval.datasets import load_dataset

    out: list[EvalTask] = []
    for name in datasets:
        out.extend(load_dataset(name, limit=limit))
    return out


def group_trials(trials: list[TrialResult]) -> dict[str, list[TrialResult]]:
    """(en) Group trials by ``task_id``. (kr) ``task_id``별 trial 그룹."""
    grouped: dict[str, list[TrialResult]] = {}
    for trial in trials:
        grouped.setdefault(trial.task_id, []).append(trial)
    return grouped


def trial_to_trace(trial: TrialResult) -> dict[str, Any]:
    """(en) Slim JSON-safe trial record for reports. (kr) 리포트용 경량 trial 레코드."""
    return {
        "trial_id": trial.trial_id,
        "task_id": trial.task_id,
        "final_content": trial.final_content[:500],
        "tool_calls": [{"name": c.name, "arguments": c.arguments} for c in trial.tool_calls],
        "turns": trial.turns,
        "input_tokens": trial.input_tokens,
        "output_tokens": trial.output_tokens,
        "total_latency_ms": round(trial.total_latency_ms, 1),
        "finished": trial.finished,
        "error": trial.error,
    }


def run_one_runner(
    runner: str,
    tasks: list[EvalTask],
    *,
    pass_k_trials: int,
    chat_fn: Callable[..., Any] | None = None,
    llm: Any | None = None,
    sleep_between_trials: float = 0.0,
    naive_max_turns: int = 8,
    harness_max_turns: int = 10,
    checkpoint: Any | None = None,
) -> tuple[list[TrialResult], dict[str, list[TrialResult]]]:
    """
    (en) Run every task `pass_k_trials` times for one runner. Returns
    (flat trials, trials grouped by task_id). Optional sleep between trials
    helps avoid Friendli serverless 429 throttling on large batches.

    (kr) 한 runner에 대해 모든 task를 `pass_k_trials`회 실행. (flat trial,
    task_id별 그룹) 반환. trial 간 sleep은 대량 배치에서 Friendli 429 throttle
    회피에 도움이 된다.
    """
    from eval.runners import harness_runner, naive_runner

    flat: list[TrialResult] = []
    grouped: dict[str, list[TrialResult]] = {}
    completed: set[str] = set()
    if checkpoint is not None:
        flat = checkpoint.load_trials(runner)
        grouped = group_trials(flat)
        completed = checkpoint.completed_trial_ids(runner)
    total = len(tasks) * pass_k_trials
    done = len(flat)
    for task in tasks:
        grouped.setdefault(task.task_id, [])
        for k in range(pass_k_trials):
            tid = f"{runner}-{task.task_id}-{k}"
            if tid in completed:
                continue
            if task.metadata.get("tau_bench"):
                from eval.runners import tau_bench_runner

                if runner == "naive":
                    if chat_fn is None:
                        raise ValueError("naive runner requires chat_fn")
                    trial = tau_bench_runner.run_trial(
                        task,
                        runner=runner,
                        trial_id=tid,
                        chat_fn=chat_fn,
                    )
                elif runner == "harness":
                    if llm is None:
                        raise ValueError("harness runner requires llm")
                    trial = tau_bench_runner.run_trial(
                        task,
                        runner=runner,
                        trial_id=tid,
                        llm=llm,
                    )
                else:
                    raise ValueError(f"unknown runner: {runner}")
            elif runner == "naive":
                if chat_fn is None:
                    raise ValueError("naive runner requires chat_fn")
                trial = naive_runner.run_trial(
                    task,
                    chat_fn=chat_fn,
                    trial_id=tid,
                    max_turns=naive_max_turns,
                )
            elif runner == "harness":
                if llm is None:
                    raise ValueError("harness runner requires llm")
                trial = harness_runner.run_trial(
                    task,
                    llm=llm,
                    trial_id=tid,
                    max_turns=harness_max_turns,
                )
            else:
                raise ValueError(f"unknown runner: {runner}")
            flat.append(trial)
            grouped[task.task_id].append(trial)
            done += 1
            if checkpoint is not None:
                checkpoint.append_trial(trial)
            if sleep_between_trials > 0 and done < total:
                time.sleep(sleep_between_trials)
    return flat, grouped


def compute_metrics(
    trials: list[TrialResult],
    grouped: dict[str, list[TrialResult]],
    tasks: list[EvalTask],
    *,
    pass_k_trials: int,
) -> dict[str, dict[str, Any]]:
    """
    (en) Apply M1–M10 to gathered trials. A metric is omitted when no task in the
    batch carries the required gold field (e.g. IFEval-only runs skip M5).

    (kr) 수집된 trial에 M1–M10 적용. batch에 필요 gold가 없으면 해당 metric은
    생략(IFEval만 돌리면 M5 제외).
    """
    from eval.judges.context_overlap import ContextTokenOverlapJudge
    from eval.judges import BFCLAnyOfJudge
    from eval.metrics import (
        m1_task_success,
        m10_empty_recovery,
        m2_pass_k,
        m3_tool_selection,
        m4_argument_f1,
        m5_abstention,
        m6_ifeval,
        m6_schema_adherence,
        m7_efficiency,
        m8_redundancy,
        m9_faithfulness,
    )
    from eval.metrics.m1_task_success import TaskGold
    from eval.metrics.m6_ifeval import IFEvalSpec, spec_from_task_metadata
    from eval.metrics.m6_schema_adherence import SchemaSpec
    from eval.metrics.m9_faithfulness import GroundingSpec
    from eval.metrics.bfcl_m1 import (
        bfcl_m1_task_ids,
        build_bfcl_m1_breakdown,
        filter_bfcl_m1_grouped,
        filter_bfcl_m1_trials,
        population_note,
    )
    from eval.metrics.types import ToolCallRecord

    out: dict[str, dict[str, Any]] = {}

    gold_calls: dict[str, list[ToolCallRecord]] = {}
    expected_no_tools: dict[str, bool] = {}
    bfcl_gold_metadata: dict[str, dict[str, Any]] = {}
    schema_specs: dict[str, SchemaSpec] = {}
    ifeval_specs: dict[str, IFEvalSpec] = {}
    grounding_specs: dict[str, GroundingSpec] = {}
    m1_golds: dict[str, TaskGold] = {}

    for t in tasks:
        if t.expected_tool_calls is not None:
            gold_calls[t.task_id] = [
                ToolCallRecord(name=c.name, arguments=dict(c.arguments))
                for c in t.expected_tool_calls
            ]
        expected_no_tools[t.task_id] = bool(t.expected_no_tools)
        if t.metadata.get("bfcl_ground_truth"):
            bfcl_gold_metadata[t.task_id] = {"bfcl_ground_truth": t.metadata["bfcl_ground_truth"]}
        if t.json_schema or t.required_keys:
            schema_specs[t.task_id] = SchemaSpec(
                required_keys=t.required_keys,
                json_schema=t.json_schema,
            )
        ifeval = spec_from_task_metadata(
            prompt=t.query,
            instructions=t.metadata.get("ifeval_instructions"),
        )
        if ifeval is not None:
            ifeval_specs[t.task_id] = ifeval
        ctx = (t.grounding_context or "").strip()
        if ctx:
            grounding_specs[t.task_id] = GroundingSpec(
                context=ctx,
                expected_answer=t.expected_answer,
            )
        if t.expected_answer is not None or t.metadata.get("bfcl_ground_truth"):
            m1_golds[t.task_id] = TaskGold(
                task_id=t.task_id,
                answer=t.expected_answer,
                rubric=t.rubric,
            )

    use_bfcl_judge = bool(bfcl_gold_metadata)
    tasks_by_id = {t.task_id: t for t in tasks}
    bfcl_task_ids = bfcl_m1_task_ids(tasks) if use_bfcl_judge else frozenset()
    bfcl_m1_gold_metadata = {
        tid: meta for tid, meta in bfcl_gold_metadata.items() if tid in bfcl_task_ids
    }
    m1_trials = filter_bfcl_m1_trials(trials, bfcl_task_ids) if bfcl_task_ids else []

    if m1_golds:
        if use_bfcl_judge and bfcl_task_ids:
            judge = BFCLAnyOfJudge()
            judge_golds = {
                tid: TaskGold(task_id=tid, answer=None, rubric=None) for tid in bfcl_task_ids
            }

            class _JudgeWrap:
                def __call__(self, *, trial, gold):
                    g = bfcl_gold_metadata.get(trial.task_id) or {}
                    return judge(trial=trial, gold=g)

            m1_summary = m1_task_success.compute(
                m1_trials, judge_golds, mode="judge", judge=_JudgeWrap()
            )
            m1_dict = m1_summary.as_dict()
            m1_dict["breakdown"] = {
                **(m1_dict.get("breakdown") or {}),
                **build_bfcl_m1_breakdown(m1_trials, tasks_by_id, bfcl_m1_gold_metadata),
            }
            m1_dict["notes"] = population_note(
                n_tasks=len(bfcl_task_ids),
                n_trials=len(m1_trials),
            )
            out["M1"] = m1_dict
        elif not use_bfcl_judge:
            m1_summary = m1_task_success.compute(trials, m1_golds, mode="exact")
            out["M1"] = m1_summary.as_dict()

    if m1_golds and pass_k_trials >= 2:
        if use_bfcl_judge and bfcl_task_ids:
            judge = BFCLAnyOfJudge()
            m1_grouped = filter_bfcl_m1_grouped(grouped, bfcl_task_ids)

            def scorer(*, trial, gold):
                g = bfcl_gold_metadata.get(trial.task_id) or {}
                return judge(trial=trial, gold=g)

            golds_for_pk = {tid: object() for tid in bfcl_task_ids}
        elif not use_bfcl_judge:

            def scorer(*, trial, gold):
                return m1_task_success.score_trial_exact(trial, gold)

            golds_for_pk = m1_golds
            m1_grouped = grouped
        else:
            golds_for_pk = {}
            m1_grouped = {}

        if golds_for_pk:
            ks = tuple(k for k in (1, 2, 4, 8) if k <= pass_k_trials)
            if len(ks) >= 2:
                m2_summary = m2_pass_k.compute(m1_grouped, golds_for_pk, scorer, ks=ks)
                m2_dict = m2_summary.as_dict()
                if use_bfcl_judge:
                    m2_dict["notes"] = (
                        population_note(n_tasks=len(bfcl_task_ids), n_trials=len(m1_trials))
                        + "; "
                        + str(m2_summary.notes)
                    )
                out["M2"] = m2_dict

    if gold_calls:
        out["M3"] = m3_tool_selection.compute(trials, gold_calls).as_dict()
        out["M4"] = m4_argument_f1.compute(trials, gold_calls).as_dict()

    if any(expected_no_tools.values()):
        out["M5"] = m5_abstention.compute(trials, expected_no_tools).as_dict()

    m6_parts = []
    if schema_specs:
        m6_parts.append(m6_schema_adherence.compute(trials, schema_specs))
    if ifeval_specs:
        m6_parts.append(m6_ifeval.compute(trials, ifeval_specs))
    if m6_parts:
        merged = m6_ifeval.merge_m6_summaries(m6_parts)
        if merged.n > 0:
            out["M6"] = merged.as_dict()

    if grounding_specs:
        m9_summary = m9_faithfulness.compute(
            trials,
            grounding_specs,
            judge=ContextTokenOverlapJudge(),
        )
        if m9_summary.n > 0:
            out["M9"] = m9_summary.as_dict()

    tsr = float(out.get("M1", {}).get("value", 0.0))
    out["M7"] = m7_efficiency.compute(trials, tsr=tsr).as_dict()
    out["M8"] = m8_redundancy.compute(trials).as_dict()

    m10_summary = m10_empty_recovery.compute(trials)
    if m10_summary.n > 0:
        out["M10"] = m10_summary.as_dict()

    return out


def run_comparison(config: RunConfig) -> ComparisonReport:
    """
    (en) End-to-end comparison: load tasks, run each runner, compute metrics,
    return a `ComparisonReport` (not yet written to disk).

    (kr) end-to-end 비교: task 로드, runner 실행, metric 계산 후 `ComparisonReport`
    반환(디스크 저장은 호출자 책임).
    """
    tasks = gather_tasks(config.datasets, config.limit)
    if not tasks:
        raise ValueError("No tasks loaded — check datasets / limit.")

    checkpoint = None
    if config.checkpoint:
        from eval.checkpoint import RunCheckpoint

        base_dir = config.checkpoint_dir or Path("eval/reports")
        checkpoint = RunCheckpoint.open_or_create(
            base_dir,
            config,
            resume_run_id=config.resume_run_id,
        )
        print(f"[checkpoint] run_dir={checkpoint.run_dir}")
        checkpoint.set_trials_total(len(tasks), config.pass_k_trials)

    naive_chat_fn = None
    harness_llm = None
    if "naive" in config.runners:
        from eval.runners.naive_runner import make_friendli_chat_fn

        naive_chat_fn = make_friendli_chat_fn()
    if "harness" in config.runners:
        from eval.runners.harness_runner import make_exaone_client

        harness_llm = make_exaone_client()

    summaries: dict[str, RunnerSummary] = {}
    all_trials: dict[str, list[dict[str, Any]]] = {}
    any_partial = False

    print(f"Loaded {len(tasks)} task(s) from {list(config.datasets)}.")

    for runner in config.runners:
        t0 = time.monotonic()
        expected_trials = len(tasks) * config.pass_k_trials
        if checkpoint is not None and checkpoint.is_runner_complete(
            runner,
            n_tasks=len(tasks),
            pass_k_trials=config.pass_k_trials,
        ):
            trials = checkpoint.load_trials(runner)
            grouped = group_trials(trials)
            print(f"[{runner}] resumed from checkpoint ({len(trials)} trials)")
        else:
            print(
                f"[{runner}] running {len(tasks)} task(s) × {config.pass_k_trials} trial(s)..."
            )
            logger.info(
                "[%s] %d task(s) × %d trial(s)",
                runner,
                len(tasks),
                config.pass_k_trials,
            )
            trials, grouped = run_one_runner(
                runner,
                tasks,
                pass_k_trials=config.pass_k_trials,
                chat_fn=naive_chat_fn,
                llm=harness_llm,
                sleep_between_trials=config.sleep_between_trials,
                naive_max_turns=config.naive_max_turns,
                harness_max_turns=config.harness_max_turns,
                checkpoint=checkpoint,
            )
        elapsed = time.monotonic() - t0
        print(f"[{runner}] done in {elapsed:.1f}s ({len(trials)} trials)")
        logger.info("[%s] finished in %.1fs (%d trials)", runner, elapsed, len(trials))
        runner_partial = len(trials) < expected_trials
        any_partial = any_partial or runner_partial
        metric_dicts = compute_metrics(
            trials, grouped, tasks, pass_k_trials=config.pass_k_trials
        )
        summaries[runner] = RunnerSummary(
            runner=runner,
            metrics=enrich_metrics(metric_dicts),
        )
        all_trials[runner] = [trial_to_trace(t) for t in trials]
        if checkpoint is not None:
            checkpoint.save_runner_summary(runner, metric_dicts, partial=runner_partial)
            if not runner_partial:
                checkpoint.mark_runner_complete(runner)
            partial_report = checkpoint.build_comparison_report(
                config,
                tasks,
                summaries,
                partial=any_partial,
            )
            latest_path = checkpoint.write_latest(partial_report)
            print(f"[checkpoint] updated {latest_path}")

    report = ComparisonReport(
        timestamp=timestamp_from_run_id(checkpoint.run_id) if checkpoint else utc_timestamp(),
        datasets=list(config.datasets),
        limit=config.limit,
        pass_k_trials=config.pass_k_trials,
        n_tasks=len(tasks),
        model=os.environ.get("EXAONE_MODEL", "?"),
        base_url_slug=slug_endpoint(os.environ.get("EXAONE_BASE_URL", "")),
        runners=list(config.runners),
        summaries=summaries,
        deltas=compute_deltas(summaries),
        trials=all_trials,
        partial=any_partial,
        checkpoint_run_id=checkpoint.run_id if checkpoint else None,
    )
    if checkpoint is not None:
        if not any_partial:
            checkpoint.finalize(report)
        else:
            checkpoint.write_latest(report)
    return report


__all__ = [
    "RunConfig",
    "gather_tasks",
    "group_trials",
    "trial_to_trace",
    "run_one_runner",
    "compute_metrics",
    "run_comparison",
]
