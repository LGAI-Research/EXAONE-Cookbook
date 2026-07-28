"""
(en) Comparison report types, display normalization (M1–M10 all ↑ higher is better),
Markdown/JSON writers.

(kr) 비교 리포트 타입, 표시 정규화(M1–M10 모두 ↑ 높을수록 좋음), Markdown/JSON writer.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

# Stable column order for Markdown tables (M10 reserved; omitted when not computed).
METRIC_ORDER: tuple[str, ...] = (
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M7",
    "M8",
    "M9",
    "M10",
)

DISPLAY_NAMES: dict[str, str] = {
    "M1": "Task Success Rate",
    "M2": "pass^k Reliability",
    "M3": "Tool Selection Accuracy",
    "M4": "Argument F1",
    "M5": "Abstention Score",
    "M6": "Schema Adherence",
    "M7": "Token Efficiency Score",
    "M8": "Call Uniqueness Score",
    "M9": "Faithfulness Score",
    "M10": "Empty-response Recovery Score",
}


def display_value(metric_id: str, raw: Mapping[str, Any]) -> float | None:
    """
    (en) Map internal metric `value` to the public score where **higher is better**.
    M8 stores redundancy (lower is better); display uses `1 - redundancy`.

    (kr) 내부 metric `value`를 공개 스코어(↑ 좋음)로 변환. M8은 redundancy 저장,
    표시는 `1 - redundancy`.
    """
    try:
        v = float(raw["value"])
    except (KeyError, TypeError, ValueError):
        return None
    if metric_id == "M8":
        return 1.0 - v
    return v


def enrich_metrics(metrics: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """
    (en) Attach `display_name` and `display_value` on each metric dict (in-place copy).

    (kr) 각 metric dict에 `display_name`, `display_value`를 붙인 복사본 반환.
    """
    out: dict[str, dict[str, Any]] = {}
    for mid, raw in metrics.items():
        enriched = dict(raw)
        enriched["display_name"] = DISPLAY_NAMES.get(mid, str(raw.get("name", mid)))
        dv = display_value(mid, raw)
        enriched["display_value"] = dv
        if mid == "M8" and dv is not None:
            breakdown = dict(enriched.get("breakdown") or {})
            breakdown["call_uniqueness"] = dv
            breakdown["redundancy_rate"] = float(raw["value"])
            enriched["breakdown"] = breakdown
        out[mid] = enriched
    return out


@dataclass
class RunnerSummary:
    """(en) Per-runner metric summaries. (kr) runner별 metric 요약."""

    runner: str
    metrics: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class ComparisonReport:
    """
    (en) On-disk comparison artefact: config, per-runner summaries, harness−naive
    deltas (on display_value), and per-trial traces.

    (kr) 디스크 비교 산출물: 설정, runner별 요약, harness−naive delta(display_value
    기준), per-trial trace.
    """

    timestamp: str
    datasets: list[str]
    limit: int | None
    pass_k_trials: int
    n_tasks: int
    model: str
    base_url_slug: str
    runners: list[str]
    summaries: dict[str, RunnerSummary]
    deltas: dict[str, float]
    trials: dict[str, list[dict[str, Any]]]
    partial: bool = False
    checkpoint_run_id: str | None = None
    merged_from: list[str] | None = None


def compute_deltas(summaries: dict[str, RunnerSummary]) -> dict[str, float]:
    """
    (en) harness − naive on `display_value` for every shared metric. Positive ⇒ harness better.

    (kr) 공통 metric의 `display_value`에 대한 harness − naive. 양수 ⇒ harness 우위.
    """
    if "naive" not in summaries or "harness" not in summaries:
        return {}
    naive_m = summaries["naive"].metrics
    harness_m = summaries["harness"].metrics
    out: dict[str, float] = {}
    for mid in sorted(set(naive_m) & set(harness_m)):
        nv = display_value(mid, naive_m[mid])
        hv = display_value(mid, harness_m[mid])
        if nv is not None and hv is not None:
            out[mid] = hv - nv
    return out


def markdown_table(report: ComparisonReport) -> str:
    """(en) Human-readable comparison table. (kr) 사람이 읽기 쉬운 비교 표."""
    lines = [
        "# Comparison Report",
        "",
        f"- **Datasets**: {', '.join(report.datasets)}",
        f"- **n_tasks**: {report.n_tasks}, **trials/task/runner**: {report.pass_k_trials}",
        f"- **model**: `{report.model}`",
        f"- **endpoint**: `{report.base_url_slug}`",
        f"- **timestamp**: {report.timestamp}",
    ]
    if report.checkpoint_run_id:
        lines.append(f"- **checkpoint_run_id**: `{report.checkpoint_run_id}`")
    if report.partial:
        lines.append("- **partial**: yes (run still in progress or incomplete trials)")
    if report.merged_from:
        lines.append(f"- **merged_from**: {len(report.merged_from)} checkpoint run(s)")
    lines.extend(
        [
            "",
            "All scores below are **↑ higher is better** (M8 shown as Call Uniqueness = 1 − redundancy).",
            "",
            "| ID | Metric | Naive | Harness | Δ (h − n) |",
            "|---|---|---:|---:|---:|",
        ]
    )
    naive_m = report.summaries.get("naive", RunnerSummary("naive")).metrics
    harness_m = report.summaries.get("harness", RunnerSummary("harness")).metrics
    present = sorted(set(naive_m) | set(harness_m), key=lambda m: METRIC_ORDER.index(m) if m in METRIC_ORDER else 99)
    for mid in present:
        name = DISPLAY_NAMES.get(mid, naive_m.get(mid, {}).get("display_name") or mid)
        nv = display_value(mid, naive_m[mid]) if mid in naive_m else None
        hv = display_value(mid, harness_m[mid]) if mid in harness_m else None
        delta = report.deltas.get(mid)
        delta_s = f"{delta:+.4f}" if delta is not None else "—"
        nv_s = f"{nv:.4f}" if nv is not None else "—"
        hv_s = f"{hv:.4f}" if hv is not None else "—"
        lines.append(
            f"| **{mid}** | {name} | {nv_s} | {hv_s} | {delta_s} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "- **Δ > 0** ⇒ harness is better on that metric.",
            "- M1/M2 population: BFCL `simple|multiple|parallel` tasks with `bfcl_ground_truth` only (IFEval/HaluBench/irrelevance excluded). See JSON `notes` on M1/M2.",
            "- M2 breakdown (`pass_1`, `pass_2`, …) lives in the JSON report.",
            "- M8 raw `redundancy_rate` is preserved in JSON `breakdown`.",
            "- M10 counts trials with ≥1 empty/reasoning-only trigger (`metadata.recovery`).",
            "- Metrics not applicable to the dataset batch are omitted (not zero).",
        ]
    )
    return "\n".join(lines)


def save_report(report: ComparisonReport, out_dir: Path) -> tuple[Path, Path]:
    """
    (en) Write `{timestamp}.json` and `{timestamp}.md` under `out_dir`.

    (kr) `out_dir` 아래 `{timestamp}.json`, `{timestamp}.md` 저장.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = report.timestamp.replace(":", "").replace("-", "")
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    def _encode(obj: Any) -> Any:
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        raise TypeError(repr(obj))

    json_path.write_text(
        json.dumps(report, default=_encode, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(markdown_table(report), encoding="utf-8")
    return json_path, md_path


def utc_timestamp() -> str:
    """(en) ISO-8601 UTC timestamp for report filenames. (kr) 리포트 파일명용 UTC 타임스탬프."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id_from_timestamp(ts: str) -> str:
    """(en) Filesystem-safe run id from ISO timestamp. (kr) ISO 타임스탬프 → run id."""
    return ts.replace(":", "").replace("-", "")


def timestamp_from_run_id(run_id: str) -> str:
    """
    (en) Best-effort ISO timestamp from a run id stem.

    (kr) run id stem에서 ISO 타임스탬프를 복원한다(근사).
    """
    if len(run_id) < 16 or not run_id.endswith("Z"):
        return run_id
    date = run_id[:8]
    time_part = run_id[9:-1]
    if len(time_part) >= 6:
        hh, mm, ss = time_part[:2], time_part[2:4], time_part[4:6]
        return f"{date[:4]}-{date[4:6]}-{date[6:8]}T{hh}:{mm}:{ss}Z"
    return run_id


__all__ = [
    "METRIC_ORDER",
    "DISPLAY_NAMES",
    "display_value",
    "enrich_metrics",
    "RunnerSummary",
    "ComparisonReport",
    "compute_deltas",
    "markdown_table",
    "save_report",
    "utc_timestamp",
    "run_id_from_timestamp",
    "timestamp_from_run_id",
]
