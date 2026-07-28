#!/usr/bin/env python3
"""
(en) CrewAI multi-agent demo (Researcher / Writer / Reviewer) on EXAONE. Run from cookbook root:
     ./implementations/uv_run.sh crewai python run_crew.py

(kr) EXAONE 백본 CrewAI 멀티에이전트 데모(Researcher / Writer / Reviewer)이다. cookbook 루트에서:
     ./implementations/uv_run.sh crewai python run_crew.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_CREW = Path(__file__).resolve().parent
_IMPL = _CREW.parent
for _path in (_IMPL, _CREW):
    _s = str(_path)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from common.exaone_env import load_exaone_env, openai_compat_kwargs, repo_root
from exaone_llm import build_exaone_llm

_DEFAULT_BRIEF = _CREW / "tasks" / "research_brief_ko.md"


def _disable_crewai_telemetry() -> None:
    # (en) Opt out of CrewAI / OTEL telemetry for local EXAONE-only demos.
    # (kr) 로컬 EXAONE 전용 데모이므로 CrewAI·OTEL 텔레메트리를 끈다.
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
    os.environ.setdefault("CREWAI_TESTING", "true")


def _load_brief(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"brief file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"brief file is empty: {path}")
    return text


def _build_crew(brief: str, llm: Any) -> tuple[Any, list[Any]]:
    from crewai import Agent, Crew, Process, Task

    researcher = Agent(
        role="Researcher",
        goal="브리프를 읽고 핵심 bullet 3~5개로 요약한다.",
        backstory="한국어 기술 브리프를 구조화해 정리하는 리서처이다.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )
    writer = Agent(
        role="Writer",
        goal="리서치 요약을 바탕으로 독자 친화적인 한국어 본문을 작성한다.",
        backstory="EXAONE 에이전트 쿡북 독자를 위한 한국어 기술 라이터이다.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )
    reviewer = Agent(
        role="Reviewer",
        goal="초안의 정확성·톤·길이를 검토하고 개선된 최종본을 제시한다.",
        backstory="간결하고 정확한 한국어 기술 글을 다듬는 리뷰어이다.",
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    research_task = Task(
        description=(
            "다음 브리프를 읽고 핵심 bullet 3~5개로 요약하세요.\n\n"
            f"---\n{brief}\n---"
        ),
        expected_output="한국어 bullet 3~5개",
        agent=researcher,
    )
    write_task = Task(
        description=(
            "리서치 요약을 바탕으로 3문단 한국어 소개글을 작성하세요. "
            "각 문단은 2~3문장으로 유지하세요."
        ),
        expected_output="3문단 한국어 본문",
        agent=writer,
        context=[research_task],
    )
    review_task = Task(
        description=(
            "작성된 본문을 검토하고, 톤·사실·길이를 다듬은 최종본을 제시하세요."
        ),
        expected_output="다듬어진 최종 한국어 본문",
        agent=reviewer,
        context=[write_task],
    )

    tasks = [research_task, write_task, review_task]
    crew = Crew(
        agents=[researcher, writer, reviewer],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=False,
    )
    return crew, tasks


def _serialize_trace(
    result: Any,
    *,
    model: str,
    brief_path: Path,
    dry_run: bool,
) -> dict[str, Any]:
    tasks_out: list[dict[str, str]] = []
    if not dry_run and hasattr(result, "tasks_output"):
        for item in result.tasks_output:
            tasks_out.append(
                {
                    "description": str(getattr(item, "description", ""))[:200],
                    "raw_preview": str(getattr(item, "raw", ""))[:800],
                }
            )
    return {
        "phase": "run_crew",
        "dry_run": dry_run,
        "model": model,
        "brief_path": str(brief_path),
        "final_output_preview": "" if dry_run else str(result)[:2000],
        "tasks_output": tasks_out,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CrewAI + EXAONE multi-agent demo")
    parser.add_argument(
        "--brief",
        type=Path,
        default=_DEFAULT_BRIEF,
        help="Korean research brief markdown (default: tasks/research_brief_ko.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="build agents/tasks only; skip API calls",
    )
    args = parser.parse_args()

    _disable_crewai_telemetry()
    load_exaone_env()
    kw = openai_compat_kwargs()
    brief = _load_brief(args.brief)

    if args.dry_run:
        crew, _tasks = _build_crew(brief, build_exaone_llm())
        payload = _serialize_trace(
            crew,
            model=kw["model"],
            brief_path=args.brief,
            dry_run=True,
        )
        payload["crew_agents"] = len(crew.agents)
        payload["crew_tasks"] = len(crew.tasks)
    else:
        llm = build_exaone_llm()
        crew, _tasks = _build_crew(brief, llm)
        result = crew.kickoff()
        payload = _serialize_trace(
            result,
            model=kw["model"],
            brief_path=args.brief,
            dry_run=False,
        )
        payload["ok"] = bool(str(result).strip())

    out_dir = repo_root() / "implementations" / "crewai" / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "crew_trace.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("saved:", out_path)

    if args.dry_run:
        return 0
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
