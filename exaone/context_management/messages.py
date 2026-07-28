"""
(en) Pre/post LLM context management: check and compress against ``input + reserved_new_tokens`` budget.
- input + reserved > max → error
- input + reserved > recommended → compress then proceed
- max_new_tokens capped via cap_max_new_tokens / prepare_messages_for_llm_chat
- Multi-turn: compress after each turn against the next-turn budget

(kr) LLM 호출 전/후 컨텍스트 관리 모듈이다. ``input + reserved_new_tokens`` 예산을 검사·압축한다.
- input + reserved > max → 에러
- input + reserved > recommended → 압축 후 진행
- max_new_tokens는 cap_max_new_tokens / prepare_messages_for_llm_chat로 캡한다
- 멀티턴: 다음 턴 예산 기준으로 턴 후 압축한다
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)

from exaone.context_management.constants import (
    CONTEXT_LENGTH_MAX_TOKENS,
    CONTEXT_LENGTH_RECOMMENDED_TOKENS,
    CONTEXT_TOOL_VERBATIM_MAX_TOKENS,
    CHARS_PER_TOKEN_ESTIMATE,
)
from exaone.context_management.executor import estimate_tokens_from_text, _compress_with_llm


def message_role(msg: Any) -> str:
    """
    (en) Return the role of an ExaoneMessage or dict message (lowercase).

    (kr) ExaoneMessage 또는 dict 메시지의 role을 반환한다(소문자).
    """
    if hasattr(msg, "role"):
        return str(getattr(msg, "role", "") or "").lower()
    if isinstance(msg, dict):
        return str(msg.get("role", "") or "").lower()
    return ""


def split_leading_system(messages: Sequence[Any]) -> tuple[list[Any], list[Any]]:
    """
    (en) Split leading consecutive ``role=="system"`` messages from the rest (body).
    Does not assume index 0 is system; system messages in the middle stay in body.

    (kr) 맨 앞에 연속으로 붙은 ``role=="system"`` 메시지와 나머지 body로 분리한다.
    인덱스 0이 system이라는 가정을 쓰지 않으며 중간에 있는 system은 body에 포함된다.
    """
    msgs = list(messages)
    i = 0
    while i < len(msgs) and message_role(msgs[i]) == "system":
        i += 1
    if i > 1:
        logger.warning(
            "Multiple leading system messages (%d); all are preserved during compression.",
            i,
        )
    return msgs[:i], msgs[i:]


def _has_tool_calls(msg: Any) -> bool:
    if hasattr(msg, "tool_calls"):
        return bool(getattr(msg, "tool_calls", None))
    if isinstance(msg, dict):
        return bool(msg.get("tool_calls"))
    return False


def _partition_middle_for_compression(
    messages: Sequence[Any],
) -> tuple[list[Any], list[list[Any]]]:
    """
    (en) Partition middle messages for compression into (compressible messages, tool run lists).
    A tool run is assistant (with tool_calls or followed by tool) plus consecutive tool results.

    (kr) 압축 대상 중간 메시지를 (요약 가능 메시지, tool run 목록)으로 분리한다.
    tool run은 assistant(tool_calls 또는 직후 tool)와 연속 tool 결과로 구성된다.
    """
    compressible: list[Any] = []
    tool_runs: list[list[Any]] = []
    msgs = list(messages)
    i = 0
    while i < len(msgs):
        msg = msgs[i]
        role = message_role(msg)
        next_role = message_role(msgs[i + 1]) if i + 1 < len(msgs) else ""

        if role == "assistant" and (_has_tool_calls(msg) or next_role == "tool"):
            run = [msg]
            i += 1
            while i < len(msgs) and message_role(msgs[i]) == "tool":
                run.append(msgs[i])
                i += 1
            tool_runs.append(run)
            continue

        if role == "tool":
            run = [msg]
            i += 1
            while i < len(msgs) and message_role(msgs[i]) == "tool":
                run.append(msgs[i])
                i += 1
            tool_runs.append(run)
            continue

        compressible.append(msg)
        i += 1

    return compressible, tool_runs


def _flatten_tool_runs(tool_runs: Sequence[Sequence[Any]]) -> list[Any]:
    out: list[Any] = []
    for run in tool_runs:
        out.extend(run)
    return out


def _keep_recent_tool_runs_within_budget(
    tool_runs: Sequence[Sequence[Any]],
    *,
    max_tokens: int = CONTEXT_TOOL_VERBATIM_MAX_TOKENS,
) -> list[Any]:
    if max_tokens <= 0:
        return []
    kept_reversed: list[list[Any]] = []
    used = 0
    for run in reversed(tool_runs):
        run_tokens = estimate_tokens_from_messages(run)
        if used + run_tokens > max_tokens:
            continue
        kept_reversed.append(list(run))
        used += run_tokens
    return _flatten_tool_runs(reversed(kept_reversed))


def _message_to_text(msg: Any) -> str:
    """
    (en) Convert an ExaoneMessage or role/content dict to a single-line text.

    (kr) ExaoneMessage 또는 role/content dict를 한 줄 텍스트로 변환한다.
    """
    if hasattr(msg, "content"):
        content = msg.content or ""
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        else:
            content = str(content)
        role = getattr(msg, "role", "user")
        return f"{role}: {content}"
    if isinstance(msg, dict):
        role = msg.get("role") or "user"
        content = msg.get("content") or ""
        if isinstance(content, list):
            content = " ".join(str(c) for c in content)
        return f"{role}: {content}"
    return str(msg)


def messages_to_text(messages: Sequence[Any]) -> str:
    """
    (en) Serialize a message list into one text blob for token estimation.

    (kr) 메시지 리스트를 토큰 추정용 단일 텍스트로 직렬화한다.
    """
    return "\n".join(_message_to_text(m) for m in messages)


def estimate_tokens_from_messages(messages: Sequence[Any]) -> int:
    """
    (en) Estimated token count for a message list (character-based estimate via text serialization).

    (kr) 메시지 리스트의 예상 토큰 수를 반환한다(텍스트 직렬화 기반 추정).
    """
    return estimate_tokens_from_text(messages_to_text(messages))


def max_input_tokens_for_context(
    *,
    max_context_tokens: int,
    reserved_new_tokens: int = 0,
) -> int:
    """
    (en) Maximum allowed input tokens when ``input_tokens + reserved_new_tokens <= max_context_tokens``.
    If reserved output fills the window, leave at least 1 token (or 1/4 of the window) for input.

    (kr) ``input_tokens + reserved_new_tokens <= max_context_tokens``일 때 허용되는 입력 상한이다.
    생성 예약이 창 전체를 차지하면 최소 1 토큰(또는 창의 1/4) 입력 슬롯을 남긴다.
    """
    reserved = max(0, reserved_new_tokens)
    if reserved >= max_context_tokens:
        return max(1, max_context_tokens // 4)
    return max(1, max_context_tokens - reserved)


def validate_input_tokens(
    input_tokens: int,
    *,
    max_tokens: int = CONTEXT_LENGTH_MAX_TOKENS,
    reserved_new_tokens: int = 0,
) -> str | None:
    """
    (en) Return an error message if ``input_tokens + reserved_new_tokens`` exceeds max_tokens; otherwise None.

    (kr) ``input_tokens + reserved_new_tokens``가 max_tokens를 넘으면 에러 메시지를 반환하고 이하면 None이다.
    """
    reserved = max(0, reserved_new_tokens)
    total = input_tokens + reserved
    if total <= max_tokens:
        return None
    return (
        f"입력 컨텍스트가 너무 깁니다 "
        f"(예상 입력 {input_tokens} + 생성 예약 {reserved} = {total} 토큰). "
        f"최대 {max_tokens} 토큰 이하로 줄여 주세요. "
        "긴 대화는 요약하거나 오래된 턴을 제거한 뒤 다시 시도해 주세요."
    )


def cap_max_new_tokens(
    input_tokens: int,
    requested_max: int,
    *,
    max_context_tokens: int = CONTEXT_LENGTH_MAX_TOKENS,
) -> int:
    """
    (en) Cap requested max_new_tokens so input + output does not exceed max_context_tokens.

    (kr) 요청된 max_new_tokens를 캡하여 input + output이 max_context_tokens를 넘지 않도록 한다.
    """
    remaining = max(0, max_context_tokens - input_tokens)
    return min(requested_max, remaining) if remaining > 0 else 256


def compress_messages_for_turn(
    messages: list[Any],
    llm: Any,
    *,
    keep_last_n: int = 2,
    target_max_tokens: int = CONTEXT_LENGTH_RECOMMENDED_TOKENS,
    reserved_new_tokens: int | None = None,
) -> list[Any]:
    """
    (en) Compress during multi-turn when ``input + reserved_new_tokens`` exceeds target_max_tokens (recommended window).
    Keep all leading system messages; summarize general body messages with an LLM.
    Group assistant tool calls and tool results into runs and keep some verbatim.
    Preserve the last keep_last_n body messages; if the whole body is <= keep_last_n but over budget, compress all body.

    (kr) 멀티턴 중 ``input + reserved_new_tokens``가 target_max_tokens(권장 창)를 넘을 때 압축한다.
    맨 앞 연속 system 메시지는 모두 유지하고 body의 일반 메시지는 LLM으로 요약한다.
    assistant tool 호출과 tool 결과는 한 run으로 묶어 원문으로 일부 유지한다.
    마지막 keep_last_n개(body 기준)는 그대로 유지한다.
    body 전체가 keep_last_n 이하이지만 입력 예산을 넘으면 body 전체를 압축한다.
    """
    from exaone.config import get_max_new_tokens_default
    from exaone.llm import ExaoneMessage

    if reserved_new_tokens is None:
        reserved_new_tokens = get_max_new_tokens_default()
    input_budget = max_input_tokens_for_context(
        max_context_tokens=target_max_tokens,
        reserved_new_tokens=reserved_new_tokens,
    )

    leading_system, body = split_leading_system(messages)
    estimated_input = estimate_tokens_from_messages(messages)
    if estimated_input <= input_budget:
        return list(messages)
    effective_keep_last_n = keep_last_n
    if len(body) <= keep_last_n:
        effective_keep_last_n = 0
    to_compress = (
        body[: -(effective_keep_last_n)] if effective_keep_last_n > 0 else list(body)
    )
    last_part = body[-effective_keep_last_n:] if effective_keep_last_n > 0 else []
    compressible, tool_runs = _partition_middle_for_compression(to_compress)
    kept_tool_messages = _keep_recent_tool_runs_within_budget(tool_runs)

    summary_msg = None
    text_to_compress = messages_to_text(compressible)
    if text_to_compress.strip():
        compressed_text, _ = _compress_with_llm(
            text_to_compress,
            llm,
            target_max_tokens=min(8192, input_budget // 2),
        )
        if not compressed_text.strip():
            return list(messages)
        summary_msg = ExaoneMessage(
            role="system",
            content=f"[이전 대화 요약]\n{compressed_text}",
        )
    elif not kept_tool_messages:
        return list(messages)

    out: list[Any] = []
    out.extend(leading_system)
    if summary_msg is not None:
        out.append(summary_msg)
    out.extend(kept_tool_messages)
    out.extend(last_part)

    from exaone.context_management.budget import prepare_messages_for_llm_chat

    capped, _ = prepare_messages_for_llm_chat(
        out,
        reserved_new_tokens=reserved_new_tokens,
        max_context_tokens=CONTEXT_LENGTH_MAX_TOKENS,
    )
    return capped


def ensure_input_within_limit(
    messages: list[Any],
    llm: Any,
    *,
    max_tokens: int = CONTEXT_LENGTH_MAX_TOKENS,
    recommended_tokens: int = CONTEXT_LENGTH_RECOMMENDED_TOKENS,
    reserved_new_tokens: int | None = None,
) -> tuple[list[Any], str | None]:
    """
    (en) Check and compress against ``input + reserved_new_tokens``.
    - input + reserved > max_tokens → (original, error) — do not call LLM
    - input + reserved > recommended → compress, re-check max; on pass return (compressed, None)
    - otherwise → (original, None)

    (kr) ``input + reserved_new_tokens`` 기준으로 검사·압축한다.
    - input + reserved > max_tokens → (원본, 에러)(LLM 호출 금지)
    - input + reserved > recommended → 압축 후 max 재검사, 통과 시 (압축본, None)
    - 그 외 → (원본, None)
    """
    from exaone.config import get_max_new_tokens_default

    if reserved_new_tokens is None:
        reserved_new_tokens = get_max_new_tokens_default()

    estimated = estimate_tokens_from_messages(messages)
    err = validate_input_tokens(
        estimated,
        max_tokens=max_tokens,
        reserved_new_tokens=reserved_new_tokens,
    )
    if err is not None:
        return messages, err

    recommended_input_budget = max_input_tokens_for_context(
        max_context_tokens=recommended_tokens,
        reserved_new_tokens=reserved_new_tokens,
    )
    if estimated <= recommended_input_budget:
        return messages, None

    compressed = compress_messages_for_turn(
        messages,
        llm,
        keep_last_n=1,
        target_max_tokens=recommended_tokens,
        reserved_new_tokens=reserved_new_tokens,
    )
    from exaone.context_management.budget import prepare_messages_for_llm_chat

    capped, _ = prepare_messages_for_llm_chat(
        compressed,
        reserved_new_tokens=reserved_new_tokens,
        max_context_tokens=max_tokens,
    )
    after = estimate_tokens_from_messages(capped)
    err = validate_input_tokens(
        after,
        max_tokens=max_tokens,
        reserved_new_tokens=reserved_new_tokens,
    )
    if err is not None:
        return capped, err
    return capped, None


__all__ = [
    "message_role",
    "split_leading_system",
    "messages_to_text",
    "estimate_tokens_from_messages",
    "max_input_tokens_for_context",
    "validate_input_tokens",
    "cap_max_new_tokens",
    "compress_messages_for_turn",
    "ensure_input_within_limit",
]
