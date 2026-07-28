#!/usr/bin/env python3
"""
(en) Phase 0 smoke: EXAONE env + smolagents import (no LLM call).

(kr) Phase 0 스모크: EXAONE 환경 + smolagents import(LLM 호출 없음).
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
    kw = openai_compat_kwargs()
    submodule = repo_root() / "submodules" / "smolagents"
    report: dict = {
        "repo_root": str(repo_root()),
        "model": kw["model"],
        "base_url": kw["base_url"],
        "api_key_set": bool(kw["api_key"]),
        "submodule_smolagents": submodule.is_dir(),
    }
    if not report["submodule_smolagents"]:
        report["hint_submodule"] = (
            "git clone https://github.com/huggingface/smolagents.git submodules/smolagents"
        )
    try:
        mod = importlib.import_module("smolagents")
        report["smolagents_import"] = "ok"
        report["smolagents_version"] = getattr(mod, "__version__", "unknown")
    except ImportError as exc:
        report["smolagents_import"] = f"missing: {exc}"
        report["hint"] = "uv sync --project implementations/smolagents"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    ok = report.get("smolagents_import") == "ok" and report["api_key_set"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
