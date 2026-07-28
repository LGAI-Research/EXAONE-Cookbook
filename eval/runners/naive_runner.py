"""
(en) Naive baseline runner — what a careful but plain integrator would write against
the Friendli `chat/completions` endpoint **without** any harness affordances:

- single HTTP `POST` per turn, no transport retry on empty 200 / reasoning-only.
- raw `while resp.tool_calls:` loop, no `ToolInvocationLedger` (duplicates allowed).
- no JSON repair (uses `final_content` as-is for M6 strict scoring).
- no `ThinkingRouter` / `NextStepPlanner` (no per-turn thinking gate).

A `chat_fn` callable is injected so tests can run offline (no real network).
The production factory `make_friendli_chat_fn` issues the same `requests.post`
shape that the harness uses, minus all recovery layers.

(kr) naive 기준 runner. 하네스 보조 기능 없이 신중한 통합자가 Friendli
`chat/completions`에 직접 호출했을 때의 형태.

- 턴당 단일 HTTP `POST`, 빈 200·reasoning-only에 대한 전송 계층 재시도 없음.
- 순수 `while resp.tool_calls:` 루프, `ToolInvocationLedger` 없음(중복 허용).
- JSON repair 없음(M6 strict 채점용으로 `final_content`를 그대로 사용).
- `ThinkingRouter`/`NextStepPlanner` 없음(턴별 thinking 게이트 없음).

테스트가 오프라인에서 돌도록 `chat_fn` callable을 주입받는다. 실제 운영은 팩토리
`make_friendli_chat_fn`가 하네스와 같은 `requests.post` 호출을 한다(복구 계층 일체 없음).
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Callable, Protocol

from eval.datasets.schema import EvalTask
from eval.metrics.types import ToolCallRecord, TrialResult
from eval.runners.common import (
    DEFAULT_SYSTEM_PROMPT,
    CapturedExecutor,
    make_trial,
    normalize_tool_call_args,
    retry_on_429,
    system_prompt_for,
    tools_to_schemas,
    user_content_for,
)
from eval.runners.recovery_tracking import RecoveryCounters, naive_response_needs_recovery

logger = logging.getLogger(__name__)


_DEFAULT_MAX_TURNS = 8


class ChatCallable(Protocol):
    """
    (en) Single-shot chat callable: takes OpenAI-shaped messages + tools and returns
    the raw chat-completion dict (one `choices[0]`).

    (kr) 일회성 chat callable. OpenAI 형식의 messages·tools를 받아 chat-completion dict
    (`choices[0]`) 그대로 반환한다.
    """

    def __call__(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> dict[str, Any]: ...


def make_friendli_chat_fn(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    temperature: float = 1.0,
    top_p: float = 0.95,
    max_tokens: int = 1024,
    enable_thinking: bool = True,
    timeout_s: tuple[int, int] = (10, 120),
    verify_ssl: bool | None = None,
) -> ChatCallable:
    """
    (en) Real-network chat function. Pulls credentials from env (`EXAONE_API_KEY`,
    `EXAONE_BASE_URL`, `EXAONE_MODEL`) so tests can supply their own ``chat_fn``
    without ever invoking this.

    Intentionally **does not** retry empty content / reasoning-only / 5xx —
    that's the whole point of the naive baseline.

    (kr) 실 네트워크 chat 함수. 자격증명은 환경변수(`EXAONE_API_KEY`, `EXAONE_BASE_URL`,
    `EXAONE_MODEL`)에서 읽으므로 테스트는 별도 ``chat_fn``을 넘기면 본 함수가 호출되지
    않는다.

    의도적으로 빈 content / reasoning-only / 5xx에 재시도하지 않는다. naive baseline의 핵심.
    """
    import requests

    base = (base_url or os.environ.get("EXAONE_BASE_URL") or "").rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    if not base:
        raise ValueError("EXAONE_BASE_URL required (env or argument)")
    key = api_key or os.environ.get("EXAONE_API_KEY")
    mdl = model or os.environ.get("EXAONE_MODEL")
    if not mdl:
        raise ValueError("EXAONE_MODEL required (env or argument)")

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    team = os.environ.get("FRIENDLI_TEAM_ID")
    if team:
        headers["X-Friendli-Team"] = team

    # (en) Match harness behaviour: respect DISABLE_SSL_VERIFY for corp-net TLS inspection.
    # The naive runner still does *no* retry / dedup / repair — only the TLS toggle is shared.
    # (kr) 하네스와 동일한 동작: DISABLE_SSL_VERIFY를 존중해 사내망 TLS 검사를 우회한다.
    # naive runner는 재시도/dedup/repair는 여전히 없음 — TLS 토글만 공유.
    if verify_ssl is None:
        verify_ssl = os.environ.get("DISABLE_SSL_VERIFY", "0").strip().lower() not in (
            "1",
            "true",
            "yes",
        )

    def _is_429(exc: Exception) -> bool:
        resp = getattr(exc, "response", None)
        return bool(resp is not None and getattr(resp, "status_code", None) == 429)

    def _chat(*, messages, tools):
        payload: dict[str, Any] = {
            "model": mdl,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
        }
        if tools:
            payload["tools"] = tools

        def _post():
            r = requests.post(
                f"{base}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout_s,
                verify=verify_ssl,
            )
            r.raise_for_status()
            return r.json()

        return retry_on_429(_post, is_429=_is_429)

    return _chat


def _extract_message(choice: dict[str, Any]) -> dict[str, Any]:
    return choice.get("message") or {}


def _extract_usage(resp: dict[str, Any]) -> tuple[int, int]:
    u = resp.get("usage") or {}
    return int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)


def _try_parse_json(s: str) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def run_trial(
    task: EvalTask,
    *,
    chat_fn: ChatCallable,
    max_turns: int = _DEFAULT_MAX_TURNS,
    trial_id: str | None = None,
) -> TrialResult:
    """
    (en) Execute one BFCL-style / IFEval-style / HaluBench-style task with the
    naive baseline. The loop:

    1. POST messages + tools.
    2. If the assistant returned tool_calls, run them through the stub executor,
       append assistant + tool messages, repeat.
    3. Stop when no tool_calls or `max_turns` reached.

    No retry, no dedup. ``trial_id`` lets the caller correlate multiple trials of
    the same task (used by M2 pass^k).

    (kr) 한 BFCL/IFEval/HaluBench 태스크를 naive baseline으로 실행한다. 루프:

    1. messages + tools를 POST.
    2. assistant가 tool_calls를 반환했으면 stub executor로 실행한 뒤 assistant·tool 메시지
       추가하고 반복.
    3. tool_calls가 없거나 `max_turns`에 도달하면 종료.

    재시도·dedup 없음. ``trial_id``로 같은 태스크의 복수 trial을 구분(M2 pass^k용).
    """
    tid = trial_id or f"naive-{task.task_id}-{uuid.uuid4().hex[:6]}"
    executor = CapturedExecutor(task_id=task.task_id)

    sys_prompt = system_prompt_for(task)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content_for(task)},
    ]
    tools_payload = tools_to_schemas(task.tools) if task.tools else None

    input_total = 0
    output_total = 0
    turns = 0
    final_content = ""
    error: str | None = None
    recovery = RecoveryCounters()
    t_start = time.monotonic()

    for _ in range(max_turns):
        turns += 1
        try:
            resp = chat_fn(messages=messages, tools=tools_payload)
        except Exception as e:
            error = f"chat_fn failed at turn {turns}: {e}"
            logger.warning("%s", error)
            break

        if naive_response_needs_recovery(resp):
            recovery.empty_triggers += 1

        choice = (resp.get("choices") or [{}])[0]
        msg = _extract_message(choice)
        in_tok, out_tok = _extract_usage(resp)
        input_total += in_tok
        output_total += out_tok

        content = msg.get("content") or ""
        if not isinstance(content, str):
            content = str(content)
        tool_calls = msg.get("tool_calls") or []

        if not tool_calls:
            final_content = content
            break

        assistant_entry: dict[str, Any] = {"role": "assistant", "content": content or ""}
        assistant_entry["tool_calls"] = tool_calls
        messages.append(assistant_entry)

        for call in tool_calls:
            call_id = call.get("id") or f"call_{turns}_{len(executor.calls)}"
            fn = call.get("function") or {}
            name = fn.get("name") or ""
            args = normalize_tool_call_args(fn.get("arguments"))
            result = executor(name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
    else:
        final_content = ""
        error = error or f"max_turns ({max_turns}) reached without final answer"

    total_latency_ms = (time.monotonic() - t_start) * 1000
    structured = _try_parse_json(final_content)

    return make_trial(
        task=task,
        runner="naive",
        trial_id=tid,
        final_content=final_content,
        final_structured=structured,
        captured_calls=executor.calls,
        turns=turns,
        input_tokens=input_total,
        output_tokens=output_total,
        total_latency_ms=total_latency_ms,
        finished=error is None,
        error=error,
        metadata={
            "raw_message_count": len(messages),
            "recovery": recovery.to_metadata(),
        },
    )


__all__ = [
    "ChatCallable",
    "make_friendli_chat_fn",
    "run_trial",
]
