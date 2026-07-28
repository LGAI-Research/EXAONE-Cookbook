#!/usr/bin/env python3
"""
(en) browser-use + EXAONE task runner. Run from cookbook root:
     ./implementations/uv_run.sh browser-use python run_task.py

(kr) browser-use + EXAONE 태스크 러너이다. cookbook 루트에서:
     ./implementations/uv_run.sh browser-use python run_task.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_IMPL = Path(__file__).resolve().parent.parent
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from common.exaone_env import get_disable_ssl_verify, load_exaone_env, openai_compat_kwargs, repo_root

_DEFAULT_TASK_FILE = Path(__file__).resolve().parent / "tasks" / "example_kr.yaml"


def _disable_browser_use_telemetry() -> None:
    # (en) Default off for local EXAONE-only demos (PostHog / cloud sync).
    # (kr) 로컬 EXAONE 전용 데모이므로 PostHog·클라우드 동기화는 기본 off.
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
    os.environ.setdefault("BROWSER_USE_CLOUD_SYNC", "false")


def _load_task_config(path: Path) -> dict[str, Any]:
    import yaml

    if not path.is_file():
        raise FileNotFoundError(f"task file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"task file must be a YAML mapping: {path}")
    return data


def _resolve_task_config(
    task_file: Path | None,
    inline_task: str | None,
    use_vision: bool | None,
    headless: bool | None,
) -> dict[str, Any]:
    # (en) Merge YAML defaults with CLI overrides (inline --task wins).
    # (kr) YAML 기본값과 CLI 덮어쓰기를 합친다(--task 인라인이 우선).
    cfg: dict[str, Any] = {}
    if task_file is not None:
        cfg = _load_task_config(task_file)
    if inline_task:
        cfg["task"] = inline_task
    task = (cfg.get("task") or "").strip()
    if not task:
        raise ValueError("task is empty; set --task or task: in the YAML file")
    allowed = cfg.get("allowed_domains")
    if allowed is not None and not isinstance(allowed, list):
        raise ValueError("allowed_domains must be a list of domain patterns")
    if use_vision is not None:
        cfg["use_vision"] = use_vision
    if headless is not None:
        cfg["headless"] = headless
    cfg["task"] = task
    cfg.setdefault("use_vision", False)
    cfg.setdefault("use_thinking", False)
    cfg.setdefault("headless", True)
    cfg.setdefault("max_failures", 5)
    return cfg


def _chat_openai_http_client_kwargs() -> dict[str, Any]:
    # (en) Honor DISABLE_SSL_VERIFY for browser-use ChatOpenAI (async httpx), same as exaone.llm.
    # (kr) browser-use ChatOpenAI(async httpx) 에 exaone.llm 과 동일하게 DISABLE_SSL_VERIFY 를 반영한다.
    if not get_disable_ssl_verify():
        return {}
    import httpx

    return {"http_client": httpx.AsyncClient(verify=False)}


def _serialize_history(history: Any) -> dict[str, Any]:
    # (en) Compact run summary from AgentHistoryList (browser-use 0.12.x).
    # (kr) AgentHistoryList(browser-use 0.12.x) 에서 간단 실행 요약을 만든다.
    errors = [err for err in history.errors() if err]
    return {
        "final_answer": history.final_result(),
        "is_done": history.is_done(),
        "is_successful": history.is_successful(),
        "step_count": len(history),
        "duration_seconds": history.total_duration_seconds(),
        "errors": errors,
    }


async def _run(cfg: dict[str, Any]) -> dict[str, Any]:
    from browser_use import Agent, Browser, ChatOpenAI

    kw = openai_compat_kwargs()
    llm = ChatOpenAI(
        model=kw["model"],
        base_url=kw["base_url"],
        api_key=kw["api_key"],
        remove_min_items_from_schema=True,
        **_chat_openai_http_client_kwargs(),
    )
    allowed_domains = cfg.get("allowed_domains")
    browser = Browser(
        allowed_domains=allowed_domains,
        headless=bool(cfg.get("headless", True)),
    )
    agent = Agent(
        task=str(cfg["task"]),
        llm=llm,
        browser=browser,
        use_vision=bool(cfg.get("use_vision", False)),
        use_thinking=bool(cfg.get("use_thinking", False)),
        max_failures=int(cfg.get("max_failures", 5)),
    )
    started = time.monotonic()
    history = await agent.run()
    elapsed = time.monotonic() - started
    summary = _serialize_history(history)
    return {
        "task_name": cfg.get("name"),
        "task": cfg["task"],
        "allowed_domains": allowed_domains,
        "model": kw["model"],
        "use_vision": bool(cfg.get("use_vision", False)),
        "use_thinking": bool(cfg.get("use_thinking", False)),
        "headless": bool(cfg.get("headless", True)),
        "elapsed_seconds": round(elapsed, 2),
        **summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="browser-use + EXAONE demo")
    parser.add_argument(
        "--task-file",
        type=Path,
        default=_DEFAULT_TASK_FILE,
        help="YAML task definition (default: tasks/example_kr.yaml)",
    )
    parser.add_argument(
        "--task",
        default=None,
        help="inline task text (overrides task: in YAML)",
    )
    parser.add_argument("--vision", action="store_true", help="enable use_vision on Agent")
    parser.add_argument("--no-vision", action="store_true", help="disable use_vision")
    parser.add_argument("--headless", action="store_true", help="run browser headless (default from YAML)")
    parser.add_argument("--no-headless", action="store_true", help="show browser window")
    args = parser.parse_args()

    use_vision: bool | None = None
    if args.vision:
        use_vision = True
    elif args.no_vision:
        use_vision = False

    headless: bool | None = None
    if args.headless:
        headless = True
    elif args.no_headless:
        headless = False

    _disable_browser_use_telemetry()
    load_exaone_env()
    cfg = _resolve_task_config(args.task_file, args.task, use_vision, headless)
    payload = asyncio.run(_run(cfg))

    out_dir = repo_root() / "implementations" / "browser-use" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "run.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "task_name": payload.get("task_name"),
                "final_answer": payload.get("final_answer"),
                "is_successful": payload.get("is_successful"),
                "saved": str(out_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    # (en) Pass when the agent finished successfully; transient step errors may remain in history.
    # (kr) 에이전트가 성공 종료하면 통과; history 에 일시적 step 오류가 남을 수 있다.
    if payload.get("is_successful") is True:
        return 0
    if payload.get("is_successful") is False or payload.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
