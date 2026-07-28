"""
(en) Loader for τ-bench (`sierra-research/tau-bench`) retail / airline domains.

Each row becomes an ``EvalTask`` with gold tool trajectory in ``expected_tool_calls``
and ``expected_answer=1`` (reward). Run via ``eval.runners.tau_bench_runner`` — not the
BFCL single-shot loop.

Install: ``uv pip install '.[eval-taubench]'`` or
``uv pip install git+https://github.com/sierra-research/tau-bench.git``.

(kr) τ-bench(`sierra-research/tau-bench`) retail / airline 로더.

각 row는 ``EvalTask``로 변환되며 gold tool 궤적은 ``expected_tool_calls``,
``expected_answer=1``(reward)에 담긴다. BFCL 단발 루프가 아니라
``eval.runners.tau_bench_runner``로 실행한다.

설치: ``uv pip install '.[eval-taubench]'`` 또는
``uv pip install git+https://github.com/sierra-research/tau-bench.git``.
"""
from __future__ import annotations

import os
from typing import Any

from .schema import EvalTask, ExpectedToolCall, ToolSpec

TAU_BENCH_REPO_URL = "https://github.com/sierra-research/tau-bench"
TAU_BENCH_PAPER_URL = "https://arxiv.org/abs/2406.12045"

SUPPORTED_DOMAINS: tuple[str, ...] = ("retail", "airline")

_INSTALL_HINT = (
    "tau-bench is not installed. Install with: "
    "uv pip install 'exaone-cookbook[eval-taubench]' "
    f"or uv pip install git+{TAU_BENCH_REPO_URL}.git"
)


def _ensure_tau_bench() -> None:
    try:
        import tau_bench  # noqa: F401
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc


def _task_split() -> str:
    return (os.environ.get("TAU_BENCH_TASK_SPLIT") or "test").strip() or "test"


def _user_strategy() -> str:
    return (os.environ.get("TAU_BENCH_USER_STRATEGY") or "llm").strip() or "llm"


def _user_model() -> str:
    return (
        os.environ.get("TAU_BENCH_USER_MODEL")
        or os.environ.get("EXAONE_MODEL")
        or "gpt-4o"
    ).strip()


def _tool_info_to_spec(info: dict) -> ToolSpec:
    fn = info.get("function") or {}
    return ToolSpec(
        name=str(fn.get("name") or ""),
        description=str(fn.get("description") or ""),
        parameters=fn.get("parameters") if isinstance(fn.get("parameters"), dict) else {"type": "object", "properties": {}},
    )


def _domain_env(domain: str):
    from tau_bench.envs import get_env
    from tau_bench.envs.user import UserStrategy

    return get_env(
        domain,
        user_strategy=UserStrategy.HUMAN,
        user_model="unused",
        task_split=_task_split(),
        user_provider="openai",
    )


def _task_to_eval(
    *,
    domain: str,
    task_index: int,
    task: Any,
    tools: list[ToolSpec],
    tools_info: list[dict],
    wiki: str,
) -> EvalTask:
    from tau_bench.types import RESPOND_ACTION_NAME

    expected_calls = [
        ExpectedToolCall(name=a.name, arguments=dict(a.kwargs))
        for a in task.actions
        if a.name != RESPOND_ACTION_NAME
    ]
    return EvalTask(
        task_id=f"tau_bench.{domain}.{task_index}",
        dataset=f"tau_bench.{domain}",
        category=domain,
        query=task.instruction,
        system_prompt=wiki,
        tools=tools,
        expected_tool_calls=expected_calls or None,
        expected_answer=1,
        metadata={
            "tau_bench": {
                "domain": domain,
                "task_index": task_index,
                "task_split": _task_split(),
                "user_strategy": _user_strategy(),
                "user_model": _user_model(),
                "user_id": task.user_id,
                "outputs": list(task.outputs),
            },
            "tau_bench_tools_info": tools_info,
        },
    )


def _load_domain(domain: str, *, limit: int | None) -> list[EvalTask]:
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"Unknown τ-bench domain {domain!r}; supported: {SUPPORTED_DOMAINS}")

    env = _domain_env(domain)
    tools = [_tool_info_to_spec(ti) for ti in env.tools_info]
    tools_info = list(env.tools_info)
    wiki = env.wiki

    out: list[EvalTask] = []
    for idx, task in enumerate(env.tasks):
        if limit is not None and len(out) >= limit:
            break
        out.append(
            _task_to_eval(
                domain=domain,
                task_index=idx,
                task=task,
                tools=tools,
                tools_info=tools_info,
                wiki=wiki,
            )
        )
    return out


def load(domain: str | None = None, limit: int | None = None) -> list[EvalTask]:
    """
    (en) Load τ-bench tasks for ``retail``, ``airline``, or both (``domain=None``).
    ``limit`` caps the total rows returned (across domains when ``domain`` is None).

    (kr) ``retail`` / ``airline`` 또는 둘 다(``domain=None``)의 τ-bench task를 로드한다.
    ``limit``은 반환 row 총 개수 상한(``domain=None``이면 도메인 합산)이다.
    """
    _ensure_tau_bench()
    domains = list(SUPPORTED_DOMAINS) if domain is None else [domain]
    out: list[EvalTask] = []
    remaining = limit
    for dom in domains:
        batch = _load_domain(dom, limit=remaining)
        out.extend(batch)
        if remaining is not None:
            remaining -= len(batch)
            if remaining <= 0:
                break
    return out


__all__ = ["load", "SUPPORTED_DOMAINS", "TAU_BENCH_REPO_URL", "TAU_BENCH_PAPER_URL"]
