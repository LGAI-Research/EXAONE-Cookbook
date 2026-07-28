#!/usr/bin/env python3
"""
(en) Import-only smoke for crewai glue (no EXAONE API call). Run from cookbook root:
     ./implementations/uv_run.sh crewai python scripts/check_env.py

(kr) crewai 접착 코드 import 스모크(API 호출 없음)이다. cookbook 루트에서:
     ./implementations/uv_run.sh crewai python scripts/check_env.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_CREW = Path(__file__).resolve().parent.parent
_IMPL = _CREW.parent
for _path in (_IMPL, _CREW):
    _s = str(_path)
    if _s not in sys.path:
        sys.path.insert(0, _s)


def main() -> int:
    import crewai

    from common.exaone_env import openai_compat_kwargs, repo_root
    from exaone_llm import build_exaone_llm

    kw = openai_compat_kwargs()
    llm = build_exaone_llm()
    payload = {
        "ok": True,
        "crewai_version": getattr(crewai, "__version__", "unknown"),
        "model": kw["model"],
        "llm_model_param": llm.model,
        "repo_root": str(repo_root()),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
