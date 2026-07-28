"""
(en) Incremental checkpoint I/O for long ``eval.run`` jobs: per-trial JSONL,
runner summaries, partial Markdown, resume, and merge across runs.

(kr) 장시간 ``eval.run``용 증분 체크포인트: trial별 JSONL, runner 요약,
partial Markdown, resume, run 병합.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from eval._env import slug_endpoint
from eval.datasets.schema import EvalTask
from eval.metrics.types import ToolCallRecord, TrialResult
from eval.pipeline import RunConfig, compute_metrics, gather_tasks, group_trials, trial_to_trace
from eval.report import (
    ComparisonReport,
    RunnerSummary,
    compute_deltas,
    enrich_metrics,
    markdown_table,
    run_id_from_timestamp,
    timestamp_from_run_id,
    utc_timestamp,
)

logger = logging.getLogger("eval.checkpoint")

MANIFEST_NAME = "manifest.json"
TRIALS_NAME = "trials.jsonl"
SUMMARY_NAME = "summary.json"
LATEST_MD_NAME = "latest.md"
REPORT_JSON_NAME = "report.json"


def trial_to_checkpoint_dict(trial: TrialResult) -> dict[str, Any]:
    """(en) JSON-safe full trial for checkpoint round-trip. (kr) 체크포인트 왕복용 trial dict."""
    return {
        "trial_id": trial.trial_id,
        "task_id": trial.task_id,
        "dataset": trial.dataset,
        "runner": trial.runner,
        "final_content": trial.final_content,
        "final_structured": trial.final_structured,
        "tool_calls": [
            {
                "name": c.name,
                "arguments": dict(c.arguments),
                "result_repr": c.result_repr,
                "latency_ms": c.latency_ms,
                "error": c.error,
            }
            for c in trial.tool_calls
        ],
        "turns": trial.turns,
        "input_tokens": trial.input_tokens,
        "output_tokens": trial.output_tokens,
        "total_latency_ms": trial.total_latency_ms,
        "finished": trial.finished,
        "error": trial.error,
        "metadata": dict(trial.metadata),
    }


def trial_from_checkpoint_dict(data: dict[str, Any]) -> TrialResult:
    """(en) Restore ``TrialResult`` from checkpoint JSON. (kr) 체크포인트 JSON → ``TrialResult``."""
    tool_calls = [
        ToolCallRecord(
            name=str(c.get("name") or ""),
            arguments=dict(c.get("arguments") or {}),
            result_repr=c.get("result_repr"),
            latency_ms=float(c.get("latency_ms") or 0.0),
            error=c.get("error"),
        )
        for c in data.get("tool_calls") or []
    ]
    return TrialResult(
        trial_id=str(data["trial_id"]),
        task_id=str(data["task_id"]),
        dataset=str(data.get("dataset") or ""),
        runner=str(data.get("runner") or ""),
        final_content=str(data.get("final_content") or ""),
        final_structured=data.get("final_structured"),
        tool_calls=tool_calls,
        turns=int(data.get("turns") or 0),
        input_tokens=int(data.get("input_tokens") or 0),
        output_tokens=int(data.get("output_tokens") or 0),
        total_latency_ms=float(data.get("total_latency_ms") or 0.0),
        finished=bool(data.get("finished", True)),
        error=data.get("error"),
        metadata=dict(data.get("metadata") or {}),
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _config_manifest_payload(config: RunConfig, *, run_id: str, started_at: str) -> dict[str, Any]:
    import os

    total_trials = 0
    if config.limit is not None:
        total_trials = len(config.datasets) * config.limit * config.pass_k_trials
    return {
        "run_id": run_id,
        "status": "in_progress",
        "started_at": started_at,
        "updated_at": started_at,
        "datasets": list(config.datasets),
        "limit": config.limit,
        "pass_k_trials": config.pass_k_trials,
        "runners": list(config.runners),
        "model": os.environ.get("EXAONE_MODEL", "?"),
        "base_url_slug": slug_endpoint(os.environ.get("EXAONE_BASE_URL", "")),
        "completed_runners": [],
        "progress": {
            runner: {"trials_done": 0, "trials_total": None}
            for runner in config.runners
        },
    }


def _validate_resume_config(manifest: dict[str, Any], config: RunConfig) -> None:
    expected = {
        "datasets": list(config.datasets),
        "limit": config.limit,
        "pass_k_trials": config.pass_k_trials,
        "runners": list(config.runners),
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches:
        raise ValueError(
            f"Resume config mismatch on {', '.join(mismatches)}. "
            f"manifest={ {k: manifest.get(k) for k in mismatches} }, "
            f"cli={ {k: expected[k] for k in mismatches} }"
        )


class RunCheckpoint:
    """
    (en) One checkpoint run directory under ``base_dir / run_id``.

    (kr) ``base_dir / run_id`` 아래 한 체크포인트 run 디렉터리.
    """

    def __init__(self, run_dir: Path, manifest: dict[str, Any]) -> None:
        self.run_dir = run_dir
        self.manifest = manifest

    @property
    def run_id(self) -> str:
        return str(self.manifest["run_id"])

    @classmethod
    def open_or_create(
        cls,
        base_dir: Path,
        config: RunConfig,
        *,
        resume_run_id: str | None = None,
    ) -> RunCheckpoint:
        """
        (en) Open an existing run for resume or create a new run directory.

        (kr) resume용 기존 run을 열거나 새 run 디렉터리를 만든다.
        """
        base_dir.mkdir(parents=True, exist_ok=True)
        if resume_run_id:
            run_dir = base_dir / resume_run_id
            manifest_path = run_dir / MANIFEST_NAME
            if not manifest_path.is_file():
                raise ValueError(f"Checkpoint run not found: {run_dir}")
            manifest = _read_json(manifest_path)
            _validate_resume_config(manifest, config)
            manifest["status"] = "in_progress"
            manifest["updated_at"] = _now_iso()
            _write_json(manifest_path, manifest)
            return cls(run_dir, manifest)

        started_at = utc_timestamp()
        run_id = run_id_from_timestamp(started_at)
        run_dir = base_dir / run_id
        if run_dir.exists():
            raise ValueError(f"Checkpoint run already exists: {run_dir}")
        manifest = _config_manifest_payload(config, run_id=run_id, started_at=started_at)
        _write_json(run_dir / MANIFEST_NAME, manifest)
        return cls(run_dir, manifest)

    def _runner_dir(self, runner: str) -> Path:
        return self.run_dir / runner

    def _trials_path(self, runner: str) -> Path:
        return self._runner_dir(runner) / TRIALS_NAME

    def completed_trial_ids(self, runner: str) -> set[str]:
        """(en) Trial ids already stored for ``runner``. (kr) ``runner``에 저장된 trial id."""
        return {str(row["trial_id"]) for row in _read_jsonl(self._trials_path(runner))}

    def load_trials(self, runner: str) -> list[TrialResult]:
        """(en) Load all checkpointed trials for ``runner``. (kr) ``runner`` 체크포인트 trial 로드."""
        return [trial_from_checkpoint_dict(row) for row in _read_jsonl(self._trials_path(runner))]

    def set_trials_total(self, n_tasks: int, pass_k_trials: int) -> None:
        """
        (en) Store expected trial count per runner in manifest progress.

        (kr) runner별 기대 trial 수를 manifest progress에 기록한다.
        """
        total = n_tasks * pass_k_trials
        progress = self.manifest.setdefault("progress", {})
        for runner in self.manifest.get("runners") or []:
            progress.setdefault(runner, {"trials_done": 0, "trials_total": total})[
                "trials_total"
            ] = total
        self.manifest["updated_at"] = _now_iso()
        _write_json(self.run_dir / MANIFEST_NAME, self.manifest)

    def append_trial(self, trial: TrialResult) -> None:
        """
        (en) Append one trial to JSONL and update manifest progress.

        (kr) trial 1건을 JSONL에 append하고 manifest progress를 갱신한다.
        """
        _append_jsonl(self._trials_path(trial.runner), trial_to_checkpoint_dict(trial))
        progress = self.manifest.setdefault("progress", {})
        runner_prog = progress.setdefault(trial.runner, {"trials_done": 0, "trials_total": None})
        runner_prog["trials_done"] = len(self.load_trials(trial.runner))
        self.manifest["updated_at"] = _now_iso()
        _write_json(self.run_dir / MANIFEST_NAME, self.manifest)

    def is_runner_complete(self, runner: str, *, n_tasks: int, pass_k_trials: int) -> bool:
        """(en) True when all expected trials exist for ``runner``. (kr) ``runner`` trial이 모두 있으면 True."""
        expected = n_tasks * pass_k_trials
        return len(self.load_trials(runner)) >= expected

    def save_runner_summary(
        self,
        runner: str,
        metrics: dict[str, dict[str, Any]],
        *,
        partial: bool,
    ) -> None:
        """
        (en) Write ``{runner}/summary.json`` with enriched metrics.

        (kr) enriched metric이 담긴 ``{runner}/summary.json`` 저장.
        """
        payload = {
            "runner": runner,
            "partial": partial,
            "metrics": enrich_metrics(metrics),
            "updated_at": _now_iso(),
        }
        _write_json(self._runner_dir(runner) / SUMMARY_NAME, payload)

    def mark_runner_complete(self, runner: str) -> None:
        """(en) Record runner completion in manifest. (kr) manifest에 runner 완료 표시."""
        completed = list(self.manifest.get("completed_runners") or [])
        if runner not in completed:
            completed.append(runner)
        self.manifest["completed_runners"] = completed
        self.manifest["updated_at"] = _now_iso()
        _write_json(self.run_dir / MANIFEST_NAME, self.manifest)

    def build_comparison_report(
        self,
        config: RunConfig,
        tasks: list[EvalTask],
        summaries: dict[str, RunnerSummary],
        *,
        partial: bool,
    ) -> ComparisonReport:
        """(en) Assemble a ``ComparisonReport`` from checkpointed runner summaries. (kr) 요약으로 리포트 조립."""
        all_trials: dict[str, list[dict[str, Any]]] = {}
        for runner in config.runners:
            if runner in summaries:
                trials = self.load_trials(runner)
                all_trials[runner] = [trial_to_trace(t) for t in trials]
        return ComparisonReport(
            timestamp=timestamp_from_run_id(self.run_id),
            datasets=list(config.datasets),
            limit=config.limit,
            pass_k_trials=config.pass_k_trials,
            n_tasks=len(tasks),
            model=str(self.manifest.get("model") or "?"),
            base_url_slug=str(self.manifest.get("base_url_slug") or ""),
            runners=list(config.runners),
            summaries=summaries,
            deltas=compute_deltas(summaries),
            trials=all_trials,
            partial=partial,
            checkpoint_run_id=self.run_id,
        )

    def write_latest(self, report: ComparisonReport) -> Path:
        """(en) Rewrite ``latest.md`` and ``report.json`` under the run dir. (kr) run dir에 latest/report 갱신."""
        md_path = self.run_dir / LATEST_MD_NAME
        md_path.write_text(markdown_table(report), encoding="utf-8")

        def _encode(obj: Any) -> Any:
            if hasattr(obj, "as_dict"):
                return obj.as_dict()
            if hasattr(obj, "__dataclass_fields__"):
                return asdict(obj)
            raise TypeError(repr(obj))

        json_path = self.run_dir / REPORT_JSON_NAME
        json_path.write_text(
            json.dumps(report, default=_encode, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return md_path

    def finalize(self, report: ComparisonReport) -> None:
        """(en) Mark run complete and write final checkpoint artefacts. (kr) run 완료 표시 및 최종 산출물 저장."""
        self.manifest["status"] = "complete"
        self.manifest["updated_at"] = _now_iso()
        _write_json(self.run_dir / MANIFEST_NAME, self.manifest)
        self.write_latest(report)


def merge_runs(
    run_dirs: Sequence[Path],
    *,
    out_dir: Path | None = None,
) -> ComparisonReport:
    """
    (en) Merge trials from multiple checkpoint runs (later run wins on duplicate
    ``trial_id``). Recomputes metrics from the union of trials.

    (kr) 여러 체크포인트 run의 trial을 병합(동일 ``trial_id``는 뒤 run 우선).
    합집합 trial로 metric을 재계산한다.
    """
    if not run_dirs:
        raise ValueError("At least one checkpoint run directory is required.")

    manifests = [_read_json(path / MANIFEST_NAME) for path in run_dirs]
    ref = manifests[0]
    for manifest in manifests[1:]:
        for key in ("datasets", "limit", "pass_k_trials"):
            if manifest.get(key) != ref.get(key):
                raise ValueError(
                    f"Cannot merge runs with different {key}: "
                    f"{ref.get(key)!r} vs {manifest.get(key)!r}"
                )

    datasets = tuple(str(d) for d in ref["datasets"])
    limit = ref.get("limit")
    pass_k_trials = int(ref["pass_k_trials"])
    runners: list[str] = []
    for manifest in manifests:
        for runner in manifest.get("runners") or []:
            if runner not in runners:
                runners.append(str(runner))
    if not runners:
        runners = ["naive", "harness"]
    tasks = gather_tasks(datasets, limit)

    merged_trials: dict[str, dict[str, TrialResult]] = {r: {} for r in runners}
    for run_dir in run_dirs:
        for runner in runners:
            for trial in RunCheckpoint(run_dir, _read_json(run_dir / MANIFEST_NAME)).load_trials(runner):
                merged_trials[runner][trial.trial_id] = trial

    summaries: dict[str, RunnerSummary] = {}
    for runner in runners:
        trials = list(merged_trials.get(runner, {}).values())
        grouped = group_trials(trials)
        metrics = compute_metrics(trials, grouped, tasks, pass_k_trials=pass_k_trials)
        summaries[runner] = RunnerSummary(runner=runner, metrics=enrich_metrics(metrics))

    report = ComparisonReport(
        timestamp=utc_timestamp(),
        datasets=list(datasets),
        limit=limit,
        pass_k_trials=pass_k_trials,
        n_tasks=len(tasks),
        model=str(ref.get("model") or "?"),
        base_url_slug=str(ref.get("base_url_slug") or ""),
        runners=runners,
        summaries=summaries,
        deltas=compute_deltas(summaries),
        trials={r: [trial_to_trace(t) for t in merged_trials.get(r, {}).values()] for r in runners},
        partial=False,
        checkpoint_run_id="merged",
        merged_from=[str(p) for p in run_dirs],
    )

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = run_id_from_timestamp(report.timestamp)
        from eval.report import save_report

        save_report(report, out_dir / f"merged_{stem}")
    return report


def print_run_status(run_dir: Path) -> None:
    """(en) Print human-readable checkpoint progress. (kr) 체크포인트 진행 상황 출력."""
    manifest = _read_json(run_dir / MANIFEST_NAME)
    print(f"run_id: {manifest.get('run_id')}")
    print(f"status: {manifest.get('status')}")
    print(f"datasets: {manifest.get('datasets')}")
    print(f"limit: {manifest.get('limit')}, pass_k_trials: {manifest.get('pass_k_trials')}")
    print(f"completed_runners: {manifest.get('completed_runners')}")
    progress = manifest.get("progress") or {}
    for runner, prog in progress.items():
        print(f"  [{runner}] {prog.get('trials_done')}/{prog.get('trials_total', '?')} trials")
    latest = run_dir / LATEST_MD_NAME
    if latest.is_file():
        print(f"latest: {latest}")


def _build_merge_parser(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("run_dirs", nargs="+", type=Path, help="checkpoint run directories to merge")
    sub.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="optional directory for merged timestamped report",
    )


def _build_status_parser(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("run_dir", type=Path, help="checkpoint run directory")


def main(argv: list[str] | None = None) -> int:
    """(en) ``python -m eval.checkpoint {merge,status}``. (kr) 체크포인트 CLI."""
    parser = argparse.ArgumentParser(description="Eval checkpoint utilities (merge, status).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    merge_parser = subparsers.add_parser("merge", help="merge trials from multiple checkpoint runs")
    _build_merge_parser(merge_parser)

    status_parser = subparsers.add_parser("status", help="show checkpoint run progress")
    _build_status_parser(status_parser)

    args = parser.parse_args(argv)
    if args.command == "merge":
        report = merge_runs(args.run_dirs, out_dir=args.out_dir)
        print(markdown_table(report))
        if args.out_dir:
            print(f"Saved merged report under: {args.out_dir}")
        return 0
    if args.command == "status":
        print_run_status(args.run_dir)
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
