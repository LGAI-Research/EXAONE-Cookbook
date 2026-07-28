#!/usr/bin/env python3
"""
(en) Phase 0 — single-turn CrewAI LLM spike against EXAONE. Run from repo root:
     PYTHONPATH=.:implementations python implementations/crewai/spike_llm.py

(kr) Phase 0 — EXAONE 대상 CrewAI LLM 1턴 스파이크이다. 레포 루트에서:
     PYTHONPATH=.:implementations python implementations/crewai/spike_llm.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_CREW = Path(__file__).resolve().parent
_IMPL = _CREW.parent
for _path in (_IMPL, _CREW):
    _s = str(_path)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from common.exaone_env import openai_compat_kwargs, repo_root
from exaone_llm import build_exaone_llm


def _disable_crewai_telemetry() -> None:
    # (en) Avoid interactive tracing prompts on first CrewAI import paths.
    # (kr) CrewAI 최초 import 경로의 대화형 tracing 프롬프트를 막는다.
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
    os.environ.setdefault("CREWAI_TESTING", "true")


def main() -> int:
    _disable_crewai_telemetry()
    kw = openai_compat_kwargs()
    llm = build_exaone_llm()
    prompt = "한 문장으로 답하세요: 2+2는?"
    answer = llm.call(prompt)

    payload = {
        "phase": "spike_llm",
        "ok": bool(str(answer).strip()),
        "model": kw["model"],
        "prompt": prompt,
        "answer_preview": str(answer)[:500],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = repo_root() / "implementations" / "crewai" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "spike_llm.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("saved:", out_path)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
