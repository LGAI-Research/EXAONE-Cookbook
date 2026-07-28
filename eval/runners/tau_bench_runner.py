"""
(en) τ-bench simulation runner — drives ``tau_bench.envs`` with an LLM agent and
user simulator. Produces ``TrialResult`` comparable to BFCL runners; M1 uses
``final_structured`` reward ∈ {0, 1}.

(kr) τ-bench 시뮬레이션 runner. ``tau_bench.envs``를 LLM agent·user simulator와
구동해 BFCL runner와 비교 가능한 ``TrialResult``를 만든다. M1은 ``final_structured``
reward ∈ {0, 1}을 사용한다.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Callable

from eval.datasets.schema import EvalTask
from eval.metrics.types import ToolCallRecord, TrialResult
from eval.runners.common import make_trial, retry_on_429
from eval.runners.tau_bench_litellm import patch_litellm_completion_exaone

logger = logging.getLogger(__name__)

_DEFAULT_MAX_STEPS = 30


def _tau_meta(task: EvalTask) -> dict[str, Any]:
    meta = task.metadata.get("tau_bench")
    if not isinstance(meta, dict):
        raise ValueError(f"task {task.task_id} is missing metadata['tau_bench']")
    return meta


def _max_steps() -> int:
    raw = os.environ.get("TAU_BENCH_MAX_STEPS", str(_DEFAULT_MAX_STEPS)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return _DEFAULT_MAX_STEPS


def _message_to_action(message: dict[str, Any]) -> Any:
    from tau_bench.types import RESPOND_ACTION_NAME, Action

    tool_calls = message.get("tool_calls")
    if tool_calls:
        tool_call = tool_calls[0]
        fn = tool_call.get("function") or {}
        raw_args = fn.get("arguments") or "{}"
        if isinstance(raw_args, str):
            kwargs = json.loads(raw_args) if raw_args.strip() else {}
        elif isinstance(raw_args, dict):
            kwargs = raw_args
        else:
            kwargs = {}
        return Action(name=fn.get("name") or "", kwargs=kwargs)
    content = message.get("content") or ""
    return Action(name=RESPOND_ACTION_NAME, kwargs={"content": content})


def _make_env(task: EvalTask) -> Any:
    from tau_bench.envs import get_env

    meta = _tau_meta(task)
    patch_litellm_completion_exaone()
    user_strategy = str(meta.get("user_strategy") or os.environ.get("TAU_BENCH_USER_STRATEGY") or "llm")
    user_model = str(
        meta.get("user_model")
        or os.environ.get("TAU_BENCH_USER_MODEL")
        or os.environ.get("EXAONE_MODEL")
        or "gpt-4o"
    )
    return get_env(
        str(meta["domain"]),
        user_strategy=user_strategy,
        user_model=user_model,
        user_provider="openai",
        task_split=str(meta.get("task_split") or "test"),
        task_index=int(meta["task_index"]),
    )


def _usage_from_chat_response(resp: dict[str, Any]) -> tuple[int, int]:
    usage = resp.get("usage") or {}
    return int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)


def _naive_complete(
    chat_fn: Callable[..., dict[str, Any]],
    *,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> tuple[dict[str, Any], tuple[int, int]]:
    resp = chat_fn(messages=messages, tools=tools or None)
    choice = (resp.get("choices") or [{}])[0]
    return choice.get("message") or {}, _usage_from_chat_response(resp)


def _coerce_exaone_messages(messages: list[dict[str, Any]]) -> list[Any]:
    """
    (en) τ-bench keeps OpenAI-shaped dicts; ``ExaoneAPIClient`` expects ``ExaoneMessage``.

    (kr) τ-bench는 OpenAI 형태 dict를 쓰고 ``ExaoneAPIClient``는 ``ExaoneMessage``를 기대한다.
    """
    from exaone.llm import ExaoneMessage

    out: list[ExaoneMessage] = []
    for message in messages:
        role = str(message.get("role") or "user")
        content = message.get("content")
        if content is None:
            content = ""
        out.append(
            ExaoneMessage(
                role=role,
                content=content,
                name=message.get("name"),
                tool_call_id=message.get("tool_call_id"),
                tool_calls=message.get("tool_calls"),
            )
        )
    return out


def _harness_complete(
    llm: Any,
    *,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> tuple[dict[str, Any], tuple[int, int]]:
    from eval.runners.harness_runner import _is_429_runtime_error
    from exaone.llm import ExaoneGenerateOptions

    # (en) ExaoneAPIClient expects ExaoneGenerateOptions, not a plain dict.
    # (kr) ExaoneAPIClient는 plain dict가 아니라 ExaoneGenerateOptions를 기대한다.
    options = ExaoneGenerateOptions(tools=tools or None)
    exaone_messages = _coerce_exaone_messages(messages)
    resp = retry_on_429(
        lambda: llm.chat(exaone_messages, options=options),
        is_429=_is_429_runtime_error,
    )
    msg: dict[str, Any] = {"role": "assistant", "content": getattr(resp, "content", None) or ""}
    if getattr(resp, "tool_calls", None):
        msg["tool_calls"] = resp.tool_calls
    usage = getattr(resp, "usage", None) or {}
    if isinstance(usage, dict):
        in_t = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        out_t = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    else:
        in_t = out_t = 0
    return msg, (in_t, out_t)


def run_trial(
    task: EvalTask,
    *,
    runner: str,
    trial_id: str | None = None,
    chat_fn: Callable[..., dict[str, Any]] | None = None,
    llm: Any | None = None,
    max_steps: int | None = None,
) -> TrialResult:
    """
    (en) Run one τ-bench scenario. ``runner`` must be ``naive`` (``chat_fn``) or
    ``harness`` (``llm``).

    (kr) τ-bench 시나리오 1건 실행. ``runner``는 ``naive``(``chat_fn``) 또는
    ``harness``(``llm``)여야 한다.
    """
    from tau_bench.types import RESPOND_ACTION_NAME

    if runner == "naive" and chat_fn is None:
        raise ValueError("τ-bench naive runner requires chat_fn")
    if runner == "harness" and llm is None:
        raise ValueError("τ-bench harness runner requires llm")

    tid = trial_id or f"{runner}-{task.task_id}-{uuid.uuid4().hex[:6]}"
    meta = _tau_meta(task)
    task_index = int(meta["task_index"])
    steps_cap = max_steps if max_steps is not None else _max_steps()

    env = _make_env(task)

    tools_payload = task.metadata.get("tau_bench_tools_info") or []
    wiki = task.system_prompt or ""

    t_start = time.monotonic()
    captured: list[ToolCallRecord] = []
    input_tokens = 0
    output_tokens = 0
    turns = 0
    reward = 0.0
    error: str | None = None
    final_content = ""

    try:
        reset = env.reset(task_index=task_index)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": wiki},
            {"role": "user", "content": reset.observation},
        ]

        for _ in range(steps_cap):
            turns += 1
            if runner == "naive":
                next_message, (u_in, u_out) = _naive_complete(
                    chat_fn,
                    messages=messages,
                    tools=tools_payload,
                )
            else:
                next_message, (u_in, u_out) = _harness_complete(
                    llm,
                    messages=messages,
                    tools=tools_payload,
                )
            input_tokens += u_in
            output_tokens += u_out

            action = _message_to_action(next_message)
            if action.name != RESPOND_ACTION_NAME:
                captured.append(
                    ToolCallRecord(
                        name=action.name,
                        arguments=dict(action.kwargs),
                    )
                )

            env_response = env.step(action)
            reward = float(env_response.reward)
            final_content = (
                action.kwargs.get("content", "")
                if action.name == RESPOND_ACTION_NAME
                else env_response.observation
            )

            if action.name != RESPOND_ACTION_NAME and next_message.get("tool_calls"):
                tool_call = next_message["tool_calls"][0]
                messages.extend(
                    [
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id") or f"call_{turns}",
                            "name": (tool_call.get("function") or {}).get("name") or action.name,
                            "content": env_response.observation,
                        },
                    ]
                )
            else:
                messages.extend(
                    [
                        next_message,
                        {"role": "user", "content": env_response.observation},
                    ]
                )

            if env_response.done:
                break
    except Exception as exc:
        logger.exception("τ-bench trial failed for %s", task.task_id)
        error = str(exc)

    total_latency_ms = (time.monotonic() - t_start) * 1000
    return make_trial(
        task=task,
        runner=runner,
        trial_id=tid,
        final_content=final_content,
        final_structured=reward,
        captured_calls=captured,
        turns=turns,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_latency_ms=total_latency_ms,
        finished=error is None and reward >= 1.0 - 1e-6,
        error=error,
        metadata={
            "tau_bench": dict(meta),
            "tau_bench_reward": reward,
        },
    )


__all__ = ["run_trial"]
