#!/usr/bin/env python3
"""
(en) Smoke eval for CrewAI + EXAONE (`_out/spike_llm.json`, optional `_out/crew_trace.json`).

(kr) CrewAI + EXAONE 스모크 검증(`_out/spike_llm.json`, 선택 `_out/crew_trace.json`).

Run from cookbook root:
  ./implementations/uv_run.sh crewai python eval_smoke.py
  ./implementations/uv_run.sh crewai python eval_smoke.py --run
  ./implementations/uv_run.sh crewai python eval_smoke.py --run --full
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

_IMPL = Path(__file__).resolve().parent.parent
_CREW = Path(__file__).resolve().parent
for _path in (_IMPL, _CREW):
    _s = str(_path)
    if _s not in sys.path:
        sys.path.insert(0, _s)

_exaone_env = importlib.import_module("common.exaone_env")
impl_dir = _exaone_env.impl_dir
load_exaone_env = _exaone_env.load_exaone_env
repo_root = _exaone_env.repo_root

SPIKE_JSON = Path("_out") / "spike_llm.json"
CREW_JSON = Path("_out") / "crew_trace.json"
SPIKE_SCRIPT = "spike_llm.py"
CREW_SCRIPT = "run_crew.py"


def validate_spike(payload: dict) -> list[str]:
    issues: list[str] = []
    if payload.get("phase") != "spike_llm":
        issues.append(f"phase={payload.get('phase')!r}")
    if payload.get("ok") is not True:
        issues.append("spike ok is not true")
    preview = str(payload.get("answer_preview") or "").strip()
    if not preview:
        issues.append("empty answer_preview")
    return issues


def validate_crew(payload: dict) -> list[str]:
    issues: list[str] = []
    if payload.get("phase") != "run_crew":
        issues.append(f"phase={payload.get('phase')!r}")
    if payload.get("dry_run") is True:
        issues.append("crew_trace is dry_run")
    if not str(payload.get("final_output_preview") or "").strip():
        issues.append("empty final_output_preview")
    if payload.get("ok") is not True:
        issues.append("crew ok is not true")
    return issues


def load_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path} (try --run)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object: {path}")
    return data


def run_script(script: str) -> int:
    uv_run = repo_root() / "implementations" / "uv_run.sh"
    cmd = [str(uv_run), "crewai", "python", script]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root()),
        env={**dict(__import__("os").environ), "EXAONE_IMPL_DIR": str(impl_dir())},
        check=False,
    )
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="CrewAI + EXAONE smoke eval")
    parser.add_argument(
        "--run",
        action="store_true",
        help="run spike_llm.py first (EXAONE API required)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="with --run, also run run_crew.py (3-agent crew; slower)",
    )
    args = parser.parse_args()

    load_exaone_env(caller_file=__file__)
    impl = impl_dir(caller_file=__file__)
    spike_path = impl / SPIKE_JSON
    crew_path = impl / CREW_JSON

    if args.run:
        if run_script(SPIKE_SCRIPT) != 0:
            return 1
        if args.full and run_script(CREW_SCRIPT) != 0:
            return 1

    issues: list[str] = []
    spike = load_json(spike_path, "spike_llm.json")
    issues.extend(validate_spike(spike))

    crew_report = None
    if args.full:
        if not crew_path.is_file():
            issues.append(f"missing {crew_path.name} (use --run --full)")
        else:
            crew = load_json(crew_path, "crew_trace.json")
            crew_issues = validate_crew(crew)
            issues.extend(crew_issues)
            crew_report = {
                "path": str(crew_path),
                "ok": len(crew_issues) == 0,
                "issues": crew_issues,
            }

    ok = len(issues) == 0
    report = {
        "ok": ok,
        "spike_path": str(spike_path),
        "issues": issues,
        "crew": crew_report,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
