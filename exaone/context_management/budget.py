"""
(en) LLM request context budget: input_tokens + reserved_new_tokens <= max_context_tokens.

- Above recommended: soft cap via LLM compression upstream (e.g. messages.ensure_input_within_limit).
- Above max: hard_cap_messages truncates bodies and drops messages (final defense).

(kr) LLM 요청 컨텍스트 예산 모듈이다. input_tokens + reserved_new_tokens <= max_context_tokens를 만족시킨다.

- recommended 초과: 상위(messages.ensure_input_within_limit 등)에서 LLM 압축(soft cap)을 적용한다.
- max 초과: hard_cap_messages로 본문 절단·메시지 제거(최종 방어선)를 수행한다.
"""
from __future__ import annotations

import copy
import logging
from typing import Any, Sequence

from exaone.context_management.constants import (
    CHARS_PER_TOKEN_ESTIMATE,
    CONTEXT_LENGTH_MAX_TOKENS,
)
from exaone.context_management.executor import estimate_tokens_from_text
from exaone.context_management.messages import (
    cap_max_new_tokens,
    estimate_tokens_from_messages,
    max_input_tokens_for_context,
    message_role,
    split_leading_system,
)

logger = logging.getLogger(__name__)

_TRUNCATION_SUFFIX = "\n\n[... context truncated to fit model limit ...]"


def _message_content_str(msg: Any) -> str:
    if hasattr(msg, "content"):
        content = msg.content or ""
    elif isinstance(msg, dict):
        content = msg.get("content") or ""
    else:
        return str(msg)
    if isinstance(content, list):
        return " ".join(str(c) for c in content)
    return str(content)


def _set_message_content(msg: Any, text: str) -> Any:
    if hasattr(msg, "content"):
        out = copy.copy(msg)
        out.content = text
        return out
    if isinstance(msg, dict):
        out = dict(msg)
        out["content"] = text
        return out
    return msg


def _truncate_text_to_token_budget(text: str, max_tokens: int) -> str:
    if max_tokens <= 0:
        return _TRUNCATION_SUFFIX.strip()
    if estimate_tokens_from_text(text) <= max_tokens:
        return text
    max_chars = max(1, max_tokens * CHARS_PER_TOKEN_ESTIMATE)
    suffix = _TRUNCATION_SUFFIX
    suffix_tokens = estimate_tokens_from_text(suffix)
    body_tokens = max(1, max_tokens - suffix_tokens)
    body_chars = max(1, body_tokens * CHARS_PER_TOKEN_ESTIMATE)
    if body_chars >= len(text):
        return text
    return text[:body_chars].rstrip() + suffix


def _truncate_message_to_tokens(msg: Any, max_tokens: int) -> Any:
    text = _message_content_str(msg)
    return _set_message_content(msg, _truncate_text_to_token_budget(text, max_tokens))


def hard_cap_messages(
    messages: Sequence[Any],
    *,
    max_input_tokens: int,
) -> list[Any]:
    """
    (en) Drop oldest body messages and truncate content until estimated input tokens <= max_input_tokens.
    Preserve leading consecutive system messages when possible (truncate content only if needed).

    (kr) 추정 input 토큰이 max_input_tokens 이하가 될 때까지 오래된 body 메시지를 제거하고 본문을 절단한다.
    맨 앞 연속 system은 가능한 한 유지하며 필요 시 내용만 절단한다.
    """
    if max_input_tokens <= 0:
        return []

    msgs = list(messages)
    if not msgs:
        return []

    if estimate_tokens_from_messages(msgs) <= max_input_tokens:
        return msgs

    leading_system, body = split_leading_system(msgs)
    system_msgs = [copy.copy(m) if hasattr(m, "content") else dict(m) for m in leading_system]
    body_msgs = [copy.copy(m) if hasattr(m, "content") else dict(m) for m in body]

    def _rebuild() -> list[Any]:
        return system_msgs + body_msgs

    def _fits() -> bool:
        return estimate_tokens_from_messages(_rebuild()) <= max_input_tokens

    # (en) 1) Drop oldest body messages (keep the last one)
    # (kr) 1) 오래된 body 메시지를 제거한다(마지막 1개는 유지)
    while len(body_msgs) > 1 and not _fits():
        removed = body_msgs.pop(0)
        logger.warning(
            "Hard cap: dropped oldest body message (role=%s) to fit input budget (%d tokens)",
            message_role(removed),
            max_input_tokens,
        )

    # (en) 2) Truncate remaining body messages oldest-first
    # (kr) 2) 남은 body에서 오래된 순으로 본문을 절단한다
    idx = 0
    while not _fits() and idx < len(body_msgs):
        msg = body_msgs[idx]
        msg_tokens = estimate_tokens_from_messages([msg])
        if msg_tokens <= 1:
            idx += 1
            continue
        others = estimate_tokens_from_messages(system_msgs + body_msgs[:idx] + body_msgs[idx + 1 :])
        allowance = max(1, max_input_tokens - others)
        if msg_tokens > allowance:
            body_msgs[idx] = _truncate_message_to_tokens(msg, allowance)
            logger.warning(
                "Hard cap: truncated body message[%d] (role=%s) to ~%d tokens",
                idx,
                message_role(msg),
                allowance,
            )
        idx += 1

    # (en) 3) Truncate system messages
    # (kr) 3) system 메시지를 절단한다
    s_idx = 0
    while not _fits() and s_idx < len(system_msgs):
        msg = system_msgs[s_idx]
        msg_tokens = estimate_tokens_from_messages([msg])
        others = estimate_tokens_from_messages(
            system_msgs[:s_idx] + system_msgs[s_idx + 1 :] + body_msgs
        )
        allowance = max(1, max_input_tokens - others)
        if msg_tokens > allowance:
            system_msgs[s_idx] = _truncate_message_to_tokens(msg, allowance)
            logger.warning(
                "Hard cap: truncated system message[%d] to ~%d tokens",
                s_idx,
                allowance,
            )
        s_idx += 1

    # (en) 4) Last resort: keep only the last body message and truncate the rest
    # (kr) 4) 마지막 수단. 마지막 body 메시지만 남기고 전부 절단한다
    if not _fits() and body_msgs:
        last = body_msgs[-1]
        system_tokens = estimate_tokens_from_messages(system_msgs)
        allowance = max(1, max_input_tokens - system_tokens)
        body_msgs = [_truncate_message_to_tokens(last, allowance)]
        logger.warning("Hard cap: reduced to system + last body message only")

    result = _rebuild()
    if estimate_tokens_from_messages(result) > max_input_tokens:
        # (en) Extreme overflow: replace with a minimal user stub
        # (kr) 극단적 초과 시 단일 user stub으로 대체한다
        logger.error(
            "Hard cap: still over budget (%d > %d); replacing with minimal stub",
            estimate_tokens_from_messages(result),
            max_input_tokens,
        )
        stub = _truncate_text_to_token_budget("(context truncated)", max(1, max_input_tokens))
        if system_msgs:
            system_msgs = [_truncate_message_to_tokens(system_msgs[0], max(1, max_input_tokens // 2))]
            body_msgs = [_set_message_content(body_msgs[-1] if body_msgs else {"role": "user", "content": ""}, stub)]
        else:
            return [{"role": "user", "content": stub}]
        result = system_msgs + body_msgs

    return result


def prepare_messages_for_llm_chat(
    messages: Sequence[Any],
    *,
    reserved_new_tokens: int,
    max_context_tokens: int = CONTEXT_LENGTH_MAX_TOKENS,
) -> tuple[list[Any], int]:
    """
    (en) Cap max_new_tokens and hard-cap messages so ``estimate_input + reserved_new_tokens <= max_context_tokens``.

    Returns (messages, capped_reserved_new_tokens).

    (kr) ``estimate_input + reserved_new_tokens <= max_context_tokens``를 만족하도록 max_new_tokens 캡 및 메시지 hard cap을 적용한다.

    (messages, capped_reserved_new_tokens)를 반환한다.
    """
    msgs = list(messages)
    input_tokens = estimate_tokens_from_messages(msgs)
    capped_reserved = cap_max_new_tokens(
        input_tokens,
        reserved_new_tokens,
        max_context_tokens=max_context_tokens,
    )
    max_input = max_input_tokens_for_context(
        max_context_tokens=max_context_tokens,
        reserved_new_tokens=capped_reserved,
    )
    if capped_reserved >= max_context_tokens:
        capped_reserved = max_context_tokens - max_input
        logger.warning(
            "reserved_new_tokens leaves no input room; clamped reserved to %d",
            capped_reserved,
        )

    capped_msgs = hard_cap_messages(msgs, max_input_tokens=max_input)
    final_input = estimate_tokens_from_messages(capped_msgs)
    capped_reserved = cap_max_new_tokens(
        final_input,
        reserved_new_tokens,
        max_context_tokens=max_context_tokens,
    )
    max_input = max_input_tokens_for_context(
        max_context_tokens=max_context_tokens,
        reserved_new_tokens=capped_reserved,
    )
    if final_input > max_input:
        capped_msgs = hard_cap_messages(capped_msgs, max_input_tokens=max_input)
        final_input = estimate_tokens_from_messages(capped_msgs)
        capped_reserved = cap_max_new_tokens(
            final_input,
            reserved_new_tokens,
            max_context_tokens=max_context_tokens,
        )

    if capped_msgs is not msgs or capped_reserved != reserved_new_tokens:
        logger.warning(
            "LLM context budget enforced: input %d→%d tokens, reserved %d→%d (max=%d)",
            input_tokens,
            estimate_tokens_from_messages(capped_msgs),
            reserved_new_tokens,
            capped_reserved,
            max_context_tokens,
        )
    return capped_msgs, capped_reserved
