#!/usr/bin/env python3
"""
(en) Capstone regression runner: score `data/capstone_golden.jsonl` with M1/M6/M9
(offline-friendly). Used by `10_07` and local CI examples.

(kr) 캡스톤 회귀 runner. `data/capstone_golden.jsonl`을 M1/M6/M9로 채점한다(오프라인 가능).
`10_07` 및 로컬 CI 예시에서 사용.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRACK10 = Path(__file__).resolve().parent
REPO_ROOT = TRACK10.parents[1]
GOLDEN_PATH = TRACK10 / "data" / "capstone_golden.jsonl"


def _bootstrap_path() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def load_golden(*, capstone: str | None) -> list[dict]:
    rows: list[dict] = []
    for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if capstone and row.get("capstone") not in (capstone, "all"):
            continue
        rows.append(row)
    return rows


def score_rows(rows: list[dict]) -> dict:
    from eval.metrics import m1_task_success, m6_schema_adherence, m9_faithfulness
    from eval.metrics.m1_task_success import TaskGold
    from eval.metrics.m6_schema_adherence import SchemaSpec
    from eval.metrics.m9_faithfulness import GroundingSpec, LengthRatioJudge
    from eval.metrics.types import ToolCallRecord, TrialResult

    m1_scores: list[float] = []
    m6_scores: list[float] = []
    m9_scores: list[float] = []
    case_rows: list[dict] = []

    for row in rows:
        tid = row["id"]
        content = row.get("trial_content") or str(row.get("expected_answer", ""))
        tool_calls = []
        if row.get("gold_tools"):
            tool_calls = [
                ToolCallRecord(name=g["name"], arguments=g["arguments"]) for g in row["gold_tools"]
            ]
        trial = TrialResult(
            trial_id=f"cap-{tid}",
            task_id=tid,
            dataset="track10.golden",
            runner="capstone_runner",
            final_content=content,
            tool_calls=tool_calls,
        )
        m1_val = m6_val = m9_val = None
        if row.get("expected_answer") is not None:
            m1_val = m1_task_success.score_trial_exact(
                trial, TaskGold(task_id=tid, answer=row["expected_answer"])
            )
            m1_scores.append(m1_val)
        if row.get("required_keys"):
            s, loose = m6_schema_adherence.score_trial(
                trial, SchemaSpec(required_keys=row["required_keys"])
            )
            m6_val = {"strict": s, "loose": loose}
            m6_scores.append(1.0 if loose else 0.0)
        if row.get("grounding_context"):
            m9_val = LengthRatioJudge()(
                trial=trial,
                gold={"context": row["grounding_context"]},
            )
            m9_scores.append(m9_val)
        case_rows.append({"id": tid, "capstone": row.get("capstone"), "M1": m1_val, "M6": m6_val, "M9": m9_val})

    def _mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "n_cases": len(rows),
        "summary": {
            "M1_mean": _mean(m1_scores),
            "M6_loose_mean": _mean(m6_scores),
            "M9_mean": _mean(m9_scores),
        },
        "cases": case_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track 10 capstone golden regression")
    parser.add_argument("--capstone", default=None, help="Filter e.g. 01, 02, all")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write _out/07/runner_report.json under notebook cwd or repo",
    )
    args = parser.parse_args(argv)
    _bootstrap_path()
    rows = load_golden(capstone=args.capstone)
    if len(rows) < 20 and args.capstone is None:
        print(f"warning: only {len(rows)} golden rows (recommend >= 20)", file=sys.stderr)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "capstone_filter": args.capstone,
        **score_rows(rows),
    }
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if args.write_report:
        out = TRACK10 / "_out" / "07" / "runner_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
