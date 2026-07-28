"""
(en) Unit tests for eval checkpoint I/O, resume, and merge.

(kr) eval 체크포인트 I/O·resume·merge 단위 테스트.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.checkpoint import (
    RunCheckpoint,
    merge_runs,
    trial_from_checkpoint_dict,
    trial_to_checkpoint_dict,
)
from eval.datasets.schema import EvalTask
from eval.metrics.types import TrialResult
from eval.pipeline import RunConfig, group_trials


def _trial(*, runner: str, task_id: str, k: int, reward: float) -> TrialResult:
    return TrialResult(
        trial_id=f"{runner}-{task_id}-{k}",
        task_id=task_id,
        dataset="tau_bench.retail",
        runner=runner,
        final_structured=reward,
        finished=reward >= 1.0,
    )


def _config(tmp_path: Path) -> RunConfig:
    return RunConfig(
        datasets=("tau_bench.retail",),
        limit=2,
        pass_k_trials=2,
        runners=("naive", "harness"),
        naive_max_turns=8,
        harness_max_turns=10,
        sleep_between_trials=0.0,
        checkpoint=True,
        checkpoint_dir=tmp_path,
        resume_run_id=None,
    )


def test_trial_checkpoint_round_trip():
    trial = _trial(runner="naive", task_id="tau_bench.retail.0", k=0, reward=1.0)
    restored = trial_from_checkpoint_dict(trial_to_checkpoint_dict(trial))
    assert restored.trial_id == trial.trial_id
    assert restored.final_structured == 1.0


def test_checkpoint_append_and_load(tmp_path: Path):
    config = _config(tmp_path)
    ckpt = RunCheckpoint.open_or_create(tmp_path, config)
    ckpt.set_trials_total(2, 2)
    trial = _trial(runner="naive", task_id="tau_bench.retail.0", k=0, reward=1.0)
    ckpt.append_trial(trial)

    loaded = ckpt.load_trials("naive")
    assert len(loaded) == 1
    assert loaded[0].trial_id == trial.trial_id
    assert trial.trial_id in ckpt.completed_trial_ids("naive")
    manifest = json.loads((ckpt.run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["progress"]["naive"]["trials_done"] == 1


def test_resume_rejects_config_mismatch(tmp_path: Path):
    config = _config(tmp_path)
    ckpt = RunCheckpoint.open_or_create(tmp_path, config)
    run_id = ckpt.run_id

    bad = RunConfig(
        datasets=("tau_bench.retail",),
        limit=3,
        pass_k_trials=2,
        runners=("naive", "harness"),
        naive_max_turns=8,
        harness_max_turns=10,
        sleep_between_trials=0.0,
        checkpoint=True,
        checkpoint_dir=tmp_path,
        resume_run_id=run_id,
    )
    with pytest.raises(ValueError, match="Resume config mismatch"):
        RunCheckpoint.open_or_create(tmp_path, bad, resume_run_id=run_id)


def test_resume_opens_existing_run(tmp_path: Path):
    config = _config(tmp_path)
    ckpt = RunCheckpoint.open_or_create(tmp_path, config)
    ckpt.append_trial(_trial(runner="naive", task_id="tau_bench.retail.0", k=0, reward=1.0))

    resumed = RunCheckpoint.open_or_create(tmp_path, config, resume_run_id=ckpt.run_id)
    assert len(resumed.load_trials("naive")) == 1
    assert resumed.manifest["status"] == "in_progress"


def test_merge_runs_unions_single_runner_checkpoints(tmp_path: Path, monkeypatch):
    stamp = iter(["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z"])
    monkeypatch.setattr("eval.checkpoint.utc_timestamp", lambda: next(stamp, "2026-01-03T00:00:00Z"))

    base = RunConfig(
        datasets=("bfcl_v3.simple",),
        limit=1,
        pass_k_trials=1,
        runners=("naive", "harness"),
        naive_max_turns=8,
        harness_max_turns=10,
        sleep_between_trials=0.0,
        checkpoint=True,
        checkpoint_dir=tmp_path,
        resume_run_id=None,
    )
    naive_cfg = RunConfig(**{**base.__dict__, "runners": ("naive",)})
    harness_cfg = RunConfig(**{**base.__dict__, "runners": ("harness",)})

    ckpt_naive = RunCheckpoint.open_or_create(tmp_path, naive_cfg)
    ckpt_naive.append_trial(_trial(runner="naive", task_id="simple_0", k=0, reward=1.0))

    ckpt_harness = RunCheckpoint.open_or_create(tmp_path, harness_cfg)
    ckpt_harness.append_trial(_trial(runner="harness", task_id="simple_0", k=0, reward=1.0))

    report = merge_runs([ckpt_naive.run_dir, ckpt_harness.run_dir])
    assert len(report.trials["naive"]) == 1
    assert len(report.trials["harness"]) == 1


def test_merge_runs_dedupes_by_trial_id(tmp_path: Path, monkeypatch):
    stamp = iter(["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z"])
    monkeypatch.setattr("eval.checkpoint.utc_timestamp", lambda: next(stamp, "2026-01-03T00:00:00Z"))

    config = _config(tmp_path)
    ckpt_a = RunCheckpoint.open_or_create(tmp_path, config)
    ckpt_a.append_trial(_trial(runner="naive", task_id="tau_bench.retail.0", k=0, reward=0.0))

    config_b = RunConfig(
        datasets=("tau_bench.retail",),
        limit=2,
        pass_k_trials=2,
        runners=("naive",),
        naive_max_turns=8,
        harness_max_turns=10,
        sleep_between_trials=0.0,
        checkpoint=True,
        checkpoint_dir=tmp_path,
        resume_run_id=None,
    )
    ckpt_b = RunCheckpoint.open_or_create(tmp_path, config_b)
    ckpt_b.append_trial(_trial(runner="naive", task_id="tau_bench.retail.0", k=0, reward=1.0))

    report = merge_runs([ckpt_a.run_dir, ckpt_b.run_dir])
    naive_trials = report.trials["naive"]
    assert len(naive_trials) == 1
    assert naive_trials[0]["trial_id"] == "naive-tau_bench.retail.0-0"


def test_group_trials_preserves_task_buckets():
    trials = [
        _trial(runner="naive", task_id="a", k=0, reward=1.0),
        _trial(runner="naive", task_id="a", k=1, reward=0.0),
        _trial(runner="naive", task_id="b", k=0, reward=1.0),
    ]
    grouped = group_trials(trials)
    assert len(grouped["a"]) == 2
    assert len(grouped["b"]) == 1


def test_build_partial_report_flags_partial(tmp_path: Path):
    config = _config(tmp_path)
    ckpt = RunCheckpoint.open_or_create(tmp_path, config)
    tasks = [
        EvalTask(task_id="tau_bench.retail.0", dataset="tau_bench.retail", category="x", query="q1"),
        EvalTask(task_id="tau_bench.retail.1", dataset="tau_bench.retail", category="x", query="q2"),
    ]
    ckpt.append_trial(_trial(runner="naive", task_id="tau_bench.retail.0", k=0, reward=1.0))
    from eval.report import RunnerSummary

    summaries = {
        "naive": RunnerSummary(runner="naive", metrics={}),
    }
    report = ckpt.build_comparison_report(config, tasks, summaries, partial=True)
    assert report.partial is True
    assert report.checkpoint_run_id == ckpt.run_id
