"""
(en) LLM completion quality helpers: empty / reasoning-only detection and observability.

(kr) LLM completion 품질 헬퍼 모듈이다. 빈 응답·reasoning-only 감지 및 observability를 제공한다.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from exaone.observability import fields as obs

if TYPE_CHECKING:
    from exaone.llm.exaone_client import ExaoneResponse

logger = logging.getLogger(__name__)

FINAL_TURN_JSON_NUDGE = "[Final turn] Reply with exactly one JSON object only."
EMPTY_CONTENT_NUDGE = (
    "[Final turn] Put your final answer in message content (not reasoning only). "
    "Reply with exactly one JSON object when a schema is required."
)


def is_empty_llm_response(resp: "ExaoneResponse") -> bool:
    """
    (en) True when there is no user-facing content, reasoning, or tool calls.

    (kr) 사용자에게 보이는 content, reasoning, tool_calls가 모두 없으면 True이다.
    """
    if resp.tool_calls:
        return False
    if (resp.content or "").strip():
        return False
    if (resp.reasoning_content or "").strip():
        return False
    return True


def is_reasoning_only_llm_response(resp: "ExaoneResponse") -> bool:
    """
    (en) True when thinking is present in the reasoning channel but message content is empty.

    (kr) reasoning 채널에 사고 내용은 있으나 message content가 비어 있으면 True이다.
    """
    if resp.tool_calls:
        return False
    if (resp.content or "").strip():
        return False
    return bool((resp.reasoning_content or "").strip())


def needs_content_recovery(resp: "ExaoneResponse") -> bool:
    """
    (en) True when the client should retry (thinking-off / nudge), not promote reasoning to content.

    (kr) reasoning을 content로 승격하지 않고 클라이언트가 재시도(thinking-off / nudge)해야 하면 True이다.
    """
    return is_empty_llm_response(resp) or is_reasoning_only_llm_response(resp)


def log_llm_response_quality(
    resp: "ExaoneResponse",
    *,
    phase: str,
    enable_thinking: bool | None = None,
    recovered: bool = False,
) -> None:
    """
    (en) Emit a structured log line for dashboards (keys in exaone.observability.fields).

    (kr) 대시보드용 구조화 로그 한 줄을 남긴다(키는 exaone.observability.fields).
    """
    extra: dict[str, Any] = {
        obs.LLM_RESPONSE_PHASE: phase,
        obs.ENABLE_THINKING: enable_thinking,
        obs.LLM_FINISH_REASON: resp.finish_reason,
    }
    if is_empty_llm_response(resp):
        extra[obs.LLM_EMPTY_CONTENT] = True
        logger.warning("LLM empty content (%s)", phase, extra=extra)
    elif is_reasoning_only_llm_response(resp):
        extra[obs.LLM_REASONING_ONLY] = True
        logger.warning("LLM reasoning-only content (%s)", phase, extra=extra)
    elif recovered:
        extra[obs.LLM_EMPTY_RETRY_SUCCESS] = True
        logger.info("LLM empty-content recovery succeeded (%s)", phase, extra=extra)
