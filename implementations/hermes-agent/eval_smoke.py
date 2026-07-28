#!/usr/bin/env python3
"""
(en) Smoke eval for Hermes + EXAONE ping artifact (`_out/cli_smoke.json`).

(kr) Hermes + EXAONE ping 산출물(`_out/cli_smoke.json`) 스모크 검증.

Run from cookbook root:
  ./implementations/uv_run.sh hermes-agent python eval_smoke.py
  ./implementations/uv_run.sh hermes-agent python eval_smoke.py --run
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

SMOKE_JSON = Path("_out") / "cli_smoke.json"
GLUE = Path("scripts") / "hermes_glue.py"


def validate_payload(payload: dict) -> tuple[bool, list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    if payload.get("ok") is not True:
        issues.append("ok is not true")
    preview = str(payload.get("content_preview") or "").strip()
    if not preview:
        # (en) EXAONE may return reasoning-only with empty content — ping still counts as live OK.
        # (kr) EXAONE 이 reasoning-only 로 content 가 비어도 ping 자체는 라이브 OK 로 본다.
        warnings.append("empty content_preview (reasoning-only EXAONE — see PLAYBOOK §6.3.1)")
    if not payload.get("model"):
        issues.append("missing model")
    return len(issues) == 0, issues, warnings


def load_smoke_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"smoke artifact not found: {path} (try --run)")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"cli_smoke.json must be an object: {path}")
    return data


def run_ping_e2e() -> int:
    uv_run = repo_root() / "implementations" / "uv_run.sh"
    cmd = [str(uv_run), "hermes-agent", "python", str(GLUE), "ping"]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root()),
        env={**dict(__import__("os").environ), "EXAONE_IMPL_DIR": str(impl_dir())},
        check=False,
    )
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes + EXAONE ping smoke eval")
    parser.add_argument(
        "--run",
        action="store_true",
        help="run hermes_glue.py ping first (needs EXAONE API in impl .env)",
    )
    args = parser.parse_args()

    load_exaone_env(caller_file=__file__)
    smoke_path = impl_dir(caller_file=__file__) / SMOKE_JSON

    if args.run:
        code = run_ping_e2e()
        if code != 0:
            return code

    payload = load_smoke_json(smoke_path)
    ok, issues, warnings = validate_payload(payload)
    report = {"ok": ok, "path": str(smoke_path), "issues": issues, "warnings": warnings}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
