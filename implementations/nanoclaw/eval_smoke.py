#!/usr/bin/env python3
"""
(en) Smoke eval for NanoClaw + EXAONE turn artifact (`_out/nanoclaw_turn.json`).

(kr) NanoClaw + EXAONE 턴 산출물(`_out/nanoclaw_turn.json`) 스모크 검증.

Run from cookbook root:
  ./implementations/uv_run.sh nanoclaw python eval_smoke.py
  ./implementations/uv_run.sh nanoclaw python eval_smoke.py --run
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

DEMO_QUESTION = (
    "EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘."
)
TURN_JSON = Path("_out") / "nanoclaw_turn.json"
RUN_SCRIPT = Path(__file__).resolve().parent / "run_exaone_turn.py"


def validate_payload(payload: dict) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if payload.get("question") != DEMO_QUESTION:
        issues.append("question mismatch")
    answer = str(payload.get("answer") or "").strip()
    if not answer:
        issues.append("empty answer")
    elif len(answer) < 8:
        issues.append(f"answer too short: {answer!r}")
    if payload.get("provider") != "opencode":
        issues.append(f"provider={payload.get('provider')!r}")
    if payload.get("opencode_provider") != "exaone":
        issues.append(f"opencode_provider={payload.get('opencode_provider')!r}")
    if payload.get("channel") != "cli":
        issues.append(f"channel={payload.get('channel')!r}")
    if payload.get("success") is not True:
        issues.append("success is not true")
    return len(issues) == 0, issues


def load_turn_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"turn artifact not found: {path} (try --run)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"nanoclaw_turn.json must be an object: {path}")
    return data


def run_turn_e2e() -> int:
    uv_run = repo_root() / "implementations" / "uv_run.sh"
    cmd = [str(uv_run), "nanoclaw", "python", str(RUN_SCRIPT.name)]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root()),
        env={**dict(__import__("os").environ), "EXAONE_IMPL_DIR": str(impl_dir())},
        check=False,
    )
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="NanoClaw EXAONE turn smoke eval")
    parser.add_argument(
        "--run",
        action="store_true",
        help="run run_exaone_turn.py first (needs EXAONE API in impl .env)",
    )
    args = parser.parse_args()

    load_exaone_env(caller_file=__file__)
    turn_path = impl_dir(caller_file=__file__) / TURN_JSON

    if args.run:
        code = run_turn_e2e()
        if code != 0:
            return code

    payload = load_turn_json(turn_path)
    ok, issues = validate_payload(payload)
    report = {"ok": ok, "path": str(turn_path), "issues": issues}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
