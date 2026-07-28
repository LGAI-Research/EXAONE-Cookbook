#!/usr/bin/env python3
"""
(en) Phase 4 smoke: EXAONE env + browser-use import (no browser launch).

(kr) Phase 4 스모크: EXAONE 환경 + browser-use import(브라우저 기동 없음).
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

_IMPL = Path(__file__).resolve().parent.parent.parent
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from common.exaone_env import load_exaone_env, openai_compat_kwargs, repo_root


def main() -> int:
    load_exaone_env()
    kw = openai_compat_kwargs(require_credentials=False)
    report: dict = {
        "repo_root": str(repo_root()),
        "model": kw["model"],
        "base_url": kw["base_url"],
        "api_key_set": bool(kw["api_key"]),
    }
    if not report["api_key_set"]:
        report["hint_env"] = "cp implementations/browser-use/.env.example implementations/browser-use/.env"
    try:
        importlib.import_module("browser_use")
        report["browser_use_import"] = "ok"
    except ImportError as exc:
        report["browser_use_import"] = f"missing: {exc}"
        report["hint"] = "uv sync --project implementations/browser-use"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("browser_use_import") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
