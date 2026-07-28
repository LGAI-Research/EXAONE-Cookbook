#!/usr/bin/env python3
"""
(en) Minimal smolagents + EXAONE smoke demo. Run from cookbook root:
     ./implementations/uv_run.sh smolagents python run_agent.py

(kr) smolagents + EXAONE 최소 스모크 데모이다. cookbook 루트에서:
     ./implementations/uv_run.sh smolagents python run_agent.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

_IMPL = Path(__file__).resolve().parent.parent
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from common.exaone_env import load_exaone_env, openai_compat_kwargs, repo_root

EXPECTED_ANSWER = "282663"
DEFAULT_QUESTION = "3249 * 87은? calculator 도구를 사용해 계산해줘."


def _calculator_used(steps: list[dict[str, Any]]) -> bool:
    # (en) True if any step invoked the calculator tool.
    # (kr) 어느 step 이라도 calculator 도구를 호출했으면 True.
    for step in steps:
        for call in step.get("tool_calls") or []:
            name = call.get("name") or call.get("function", {}).get("name")
            if name == "calculator":
                return True
    return False


def _answer_matches(answer: str, expected: str = EXPECTED_ANSWER) -> bool:
    # (en) Match expected digits even if the model adds commas or Korean text.
    # (kr) 쉼표·한국어가 섞여도 기대 숫자가 포함되면 True.
    digits_only = re.sub(r"[^\d]", "", answer)
    return expected in digits_only or expected in answer


def _openai_client_kwargs() -> dict[str, Any]:
    # (en) Honor DISABLE_SSL_VERIFY for smolagents OpenAIModel (httpx), same as exaone.llm.
    # (kr) smolagents OpenAIModel(httpx) 에 exaone.llm 과 동일하게 DISABLE_SSL_VERIFY 를 반영한다.
    from exaone.config import get_disable_ssl_verify

    if not get_disable_ssl_verify():
        return {}
    import httpx

    return {"http_client": httpx.Client(verify=False)}


def main() -> int:
    load_exaone_env()
    kw = openai_compat_kwargs()

    from smolagents import OpenAIModel, ToolCallingAgent, tool

    @tool
    def calculator(expression: str) -> str:
        """Evaluate a safe arithmetic expression (digits and + - * / parentheses only).

        Args:
            expression: Arithmetic expression to evaluate, e.g. "3249 * 87".
        """
        allowed = set("0123456789+-*/(). \t")
        if not expression or any(c not in allowed for c in expression):
            return "error: unsupported characters"
        try:
            # (en) Restricted eval for demo arithmetic only (no builtins).
            # (kr) 데모용 제한 eval 이다(builtins 없음).
            value = eval(expression, {"__builtins__": {}}, {})
        except Exception as exc:
            return f"error: {exc}"
        return str(value)

    model = OpenAIModel(
        model_id=kw["model"],
        api_base=kw["base_url"],
        api_key=kw["api_key"],
        temperature=0,
        max_tokens=512,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        client_kwargs=_openai_client_kwargs(),
        flatten_messages_as_text=True,
    )
    agent = ToolCallingAgent(tools=[calculator], model=model, max_steps=5)
    question = DEFAULT_QUESTION

    # (en) Thinking is off — expect ~5–15s total; do not Ctrl+C during the final LLM turn.
    # (kr) thinking 은 꺼져 있음 — 전체 5~15초 예상; 최종 LLM 턴에서 Ctrl+C 하지 말 것.
    print("running smolagents (calculator tool + final answer; enable_thinking=false)...")

    started = time.monotonic()
    try:
        run_result = agent.run(question, return_full_result=True)
    except Exception as exc:
        elapsed = time.monotonic() - started
        out_dir = repo_root() / "implementations" / "smolagents" / "_out"
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "question": question,
            "expected": EXPECTED_ANSWER,
            "answer": None,
            "model": kw["model"],
            "calculator_used": False,
            "answer_ok": False,
            "agent_state": "error",
            "success": False,
            "error": str(exc),
            "step_count": 0,
            "elapsed_seconds": round(elapsed, 2),
        }
        out_path = out_dir / "run.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("saved:", out_path)
        return 1

    elapsed = time.monotonic() - started

    answer = str(run_result.output)
    steps = run_result.steps or []
    calculator_used = _calculator_used(steps)
    answer_ok = _answer_matches(answer)
    # (en) Smoke pass = tool used + correct digits; agent_state may be max_steps_error on 236B JSON quirks.
    # (kr) 스모크 통과 = 도구 사용 + 정답 숫자; 236B JSON 깨짐 시 agent_state 는 max_steps_error 일 수 있다.
    success = calculator_used and answer_ok

    out_dir = repo_root() / "implementations" / "smolagents" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "question": question,
        "expected": EXPECTED_ANSWER,
        "answer": answer,
        "model": kw["model"],
        "calculator_used": calculator_used,
        "answer_ok": answer_ok,
        "agent_state": run_result.state,
        "success": success,
        "step_count": len(steps),
        "elapsed_seconds": round(elapsed, 2),
    }
    out_path = out_dir / "run.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("saved:", out_path)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
