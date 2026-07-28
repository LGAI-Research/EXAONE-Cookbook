#!/usr/bin/env python3
"""
(en) Smoke eval for browser-use + EXAONE (`_out/run.json`).

(kr) browser-use + EXAONE 스모크 검증(`_out/run.json`).

Run from cookbook root:
  ./implementations/uv_run.sh browser-use python eval_smoke.py
  ./implementations/uv_run.sh browser-use python eval_smoke.py --run
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

_IMPL = Path(__file__).resolve().parent.parent
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

_exaone_env = importlib.import_module("common.exaone_env")
impl_dir = _exaone_env.impl_dir
load_exaone_env = _exaone_env.load_exaone_env
repo_root = _exaone_env.repo_root

RUN_JSON = Path("_out") / "run.json"
RUN_SCRIPT = "run_task.py"
EXPECTED_TASK_NAME = "example_kr"


def validate_payload(payload: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    if payload.get("task_name") != EXPECTED_TASK_NAME:
        issues.append(f"task_name={payload.get('task_name')!r}")
    allowed = payload.get("allowed_domains") or []
    if not any("example.com" in str(d) for d in allowed):
        issues.append("allowed_domains missing example.com")
    if payload.get("is_successful") is not True:
        issues.append(f"is_successful={payload.get('is_successful')!r}")
    answer = str(payload.get("final_answer") or "").strip()
    if not answer:
        issues.append("empty final_answer")
    elif len(answer) < 8:
        issues.append(f"final_answer too short: {answer!r}")
    errors = [e for e in (payload.get("errors") or []) if e]
    if errors:
        # (en) Warn only when the run still finished successfully (236B structured-output quirks).
        # (kr) 실행이 성공 종료됐으면 경고만(236B structured-output 특성).
        if payload.get("is_successful") is True:
            warnings.append(f"errors={errors[:3]!r}")
        else:
            issues.append(f"errors={errors[:3]!r}")
    return len(issues) == 0, issues, warnings


def load_run_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"run artifact not found: {path} (try --run)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"run.json must be an object: {path}")
    return data


def run_task_e2e() -> int:
    uv_run = repo_root() / "implementations" / "uv_run.sh"
    cmd = [str(uv_run), "browser-use", "python", RUN_SCRIPT]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root()),
        env={**dict(__import__("os").environ), "EXAONE_IMPL_DIR": str(impl_dir())},
        check=False,
    )
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="browser-use + EXAONE smoke eval")
    parser.add_argument(
        "--run",
        action="store_true",
        help="run run_task.py first (EXAONE API + Playwright required)",
    )
    args = parser.parse_args()

    load_exaone_env(caller_file=__file__)
    run_path = impl_dir(caller_file=__file__) / RUN_JSON

    if args.run:
        code = run_task_e2e()
        if code != 0:
            return code

    payload = load_run_json(run_path)
    ok, issues, warnings = validate_payload(payload)
    report = {"ok": ok, "path": str(run_path), "issues": issues, "warnings": warnings}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
