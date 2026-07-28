#!/usr/bin/env python3
"""
(en) Cookbook E2E: one EXAONE chat turn for the NanoClaw demo question.
     Proves the LLM backbone wired for Path B (OpenCode + exaone provider).
     Full Docker + `pnpm run chat` runs in YOUR NanoClaw fork — see README.md.

(kr) Cookbook E2E: NanoClaw 데모 질의로 EXAONE 1턴 호출.
     Path B(OpenCode + exaone provider)용 LLM 백본 검증.
     Docker + `pnpm run chat` 전체 E2E는 본인 fork 에서 — README.md 참고.

Run from cookbook root:
  ./implementations/uv_run.sh nanoclaw python run_exaone_turn.py
"""
from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_IMPL = Path(__file__).resolve().parent.parent
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

_exaone_env = importlib.import_module("common.exaone_env")
ensure_repo_on_path = _exaone_env.ensure_repo_on_path
load_exaone_env = _exaone_env.load_exaone_env
openai_compat_kwargs = _exaone_env.openai_compat_kwargs

DEMO_QUESTION = (
    "EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘."
)
OUT_REL = Path("_out") / "nanoclaw_turn.json"


def _extract_answer(content: str | None) -> str:
    return (content or "").strip()


def main() -> int:
    impl = load_exaone_env(caller_file=__file__)
    ensure_repo_on_path()
    kw = openai_compat_kwargs()

    from exaone.llm import ExaoneAPIClient, ExaoneMessage

    client = ExaoneAPIClient(
        base_url=kw["base_url"],
        api_key=kw["api_key"],
        model=kw["model"],
    )
    response = client.chat(
        [ExaoneMessage(role="user", content=DEMO_QUESTION)],
    )
    answer = _extract_answer(response.content)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": DEMO_QUESTION,
        "answer": answer,
        "provider": "opencode",
        "opencode_provider": "exaone",
        "model": f"exaone/{kw['model']}",
        "base_url": kw["base_url"],
        "channel": "cli",
        "integration_mode": "cookbook_exaone_llm_proof",
        "success": bool(answer),
        "note_en": (
            "Cookbook proof of EXAONE LLM for NanoClaw Path B. "
            "Container sandbox E2E: apply vendor bundle in your fork + pnpm run chat."
        ),
        "note_kr": (
            "NanoClaw Path B용 EXAONE LLM cookbook 검증. "
            "컨테이너 샌드박스 E2E는 fork 에 vendor 적용 후 pnpm run chat."
        ),
    }

    out_path = impl / OUT_REL
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"saved": str(out_path), "success": payload["success"]}, ensure_ascii=False))
    return 0 if payload["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
