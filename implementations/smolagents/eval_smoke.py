#!/usr/bin/env python3
"""
(en) Smoke eval for smolagents + EXAONE: 3249×87 via calculator tool.

(kr) smolagents + EXAONE 스모크 평가: calculator 도구로 3249×87 검증.

Run from cookbook root:
  ./implementations/uv_run.sh smolagents python eval_smoke.py
  ./implementations/uv_run.sh smolagents python eval_smoke.py --run
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_IMPL = Path(__file__).resolve().parent.parent
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from common.exaone_env import repo_root

EXPECTED_ANSWER = "282663"
RUN_JSON = repo_root() / "implementations" / "smolagents" / "_out" / "run.json"
RUN_AGENT = Path(__file__).resolve().parent / "run_agent.py"


def validate_payload(payload: dict) -> tuple[bool, list[str], list[str]]:
    # (en) Check run.json fields from run_agent.py E2E.
    # (kr) run_agent.py E2E 가 쓴 run.json 필드를 검증한다.
    issues: list[str] = []
    warnings: list[str] = []
    if str(payload.get("expected")) != EXPECTED_ANSWER:
        issues.append(f"expected={payload.get('expected')!r}, want {EXPECTED_ANSWER!r}")
    if not payload.get("calculator_used"):
        issues.append("calculator tool was not used")
    if not payload.get("answer_ok"):
        issues.append(f"answer missing {EXPECTED_ANSWER}: {payload.get('answer')!r}")
    if payload.get("agent_state") != "success":
        # (en) Warn only — 236B may finish with max_steps_error while answer_ok is still true.
        # (kr) 경고만 — 236B 는 answer_ok 인데 max_steps_error 로 끝날 수 있다.
        warnings.append(f"agent_state={payload.get('agent_state')!r}")
    if payload.get("success") is not True:
        issues.append("success is not true")
    return len(issues) == 0, issues, warnings


def load_run_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"run artifact not found: {path} (try --run)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"run.json must be an object: {path}")
    return data


def run_agent_e2e() -> int:
    # (en) Invoke run_agent.py via uv_run.sh (needs EXAONE API in impl .env).
    # (kr) uv_run.sh 로 run_agent.py 를 실행한다(impl .env 에 EXAONE API 필요).
    uv_run = repo_root() / "implementations" / "uv_run.sh"
    cmd = [str(uv_run), "smolagents", "python", "run_agent.py"]
    proc = subprocess.run(cmd, cwd=str(repo_root()), check=False)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="smolagents + EXAONE eval smoke (3249×87)")
    parser.add_argument(
        "--run",
        action="store_true",
        help="run run_agent.py first (EXAONE API required), then validate _out/run.json",
    )
    parser.add_argument(
        "--run-json",
        type=Path,
        default=RUN_JSON,
        help=f"path to run artifact (default: {RUN_JSON})",
    )
    args = parser.parse_args()

    if args.run:
        rc = run_agent_e2e()
        if rc != 0:
            print(json.dumps({"ok": False, "stage": "run_agent", "exit_code": rc}, indent=2))
            return rc

    try:
        payload = load_run_json(args.run_json)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    ok, issues, warnings = validate_payload(payload)
    report = {
        "ok": ok,
        "run_json": str(args.run_json),
        "expected": EXPECTED_ANSWER,
        "calculator_used": payload.get("calculator_used"),
        "answer_ok": payload.get("answer_ok"),
        "success": payload.get("success"),
        "issues": issues,
        "warnings": warnings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
