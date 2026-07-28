"""
(en) Recovery counters for M10 — shared between naive and harness eval runners.

Harness uses ``EvalRecoveryTrackingClient`` (eval-only subclass) so ``exaone/`` stays
unchanged while ``ExaoneAPIClient.chat`` retry behaviour is mirrored for metrics.

(kr) M10용 recovery 카운터 — naive·harness eval runner가 공유.

하네스는 ``EvalRecoveryTrackingClient``(eval 전용 서브클래스)로 ``exaone/`` 변경 없이
``ExaoneAPIClient.chat`` retry 동작을 메트릭용으로 추적한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class RecoveryCounters:
    """
    (en) Per-trial empty/reasoning-only triggers and successful recoveries.

    (kr) trial 단위 empty/reasoning-only trigger 및 복구 성공 횟수.
    """

    empty_triggers: int = 0
    recovery_successes: int = 0

    def reset(self) -> None:
        self.empty_triggers = 0
        self.recovery_successes = 0

    def to_metadata(self) -> dict[str, int]:
        return {
            "empty_triggers": int(self.empty_triggers),
            "recovery_successes": int(self.recovery_successes),
        }


def naive_response_needs_recovery(resp: Mapping[str, Any]) -> bool:
    """
    (en) Mirror ``needs_content_recovery`` for raw Friendli chat-completion dicts.

    (kr) raw Friendli chat-completion dict에 ``needs_content_recovery``와 동일 규칙 적용.
    """
    choice = (resp.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    tool_calls = msg.get("tool_calls") or []
    if tool_calls:
        return False
    content = msg.get("content") or ""
    if isinstance(content, str) and content.strip():
        return False
    reasoning = (
        msg.get("reasoning_content")
        or msg.get("thinking")
        or msg.get("reasoning")
        or choice.get("reasoning_content")
    )
    if isinstance(reasoning, str) and reasoning.strip():
        return True
    return not (isinstance(content, str) and content.strip())


def make_recovery_tracking_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
):
    """
    (en) ``ExaoneAPIClient`` with per-trial M10 recovery counters (eval layer only).

    (kr) trial별 M10 recovery 카운터가 붙은 ``ExaoneAPIClient``(eval 레이어만).
    """
    import os

    from exaone.context_management.messages import estimate_tokens_from_messages
    from exaone.llm import ExaoneGenerateOptions, ExaoneMessage
    from exaone.llm.exaone_client import CONTEXT_LENGTH_RECOMMENDED_TOKENS, ExaoneAPIClient
    from exaone.llm.response_quality import (
        EMPTY_CONTENT_NUDGE,
        log_llm_response_quality,
        needs_content_recovery,
    )

    class EvalRecoveryTrackingClient(ExaoneAPIClient):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self._recovery = RecoveryCounters()

        def reset_recovery_stats(self) -> None:
            self._recovery.reset()

        @property
        def recovery_stats(self) -> RecoveryCounters:
            return self._recovery

        def chat(self, messages, options=None):
            messages, opts = self._prepare_chat_request(messages, options)
            estimated_input_tokens = estimate_tokens_from_messages(messages)
            estimated_total = estimated_input_tokens + opts.max_new_tokens
            if estimated_total > CONTEXT_LENGTH_RECOMMENDED_TOKENS:
                import logging

                logging.getLogger(__name__).warning(
                    "Estimated tokens (%d input + %d output = %d) exceed "
                    "recommended limit (%d). Consider reducing context.",
                    estimated_input_tokens,
                    opts.max_new_tokens,
                    estimated_total,
                    CONTEXT_LENGTH_RECOMMENDED_TOKENS,
                )

            resp = self._execute_chat_http(messages, opts)
            log_llm_response_quality(resp, phase="initial", enable_thinking=opts.enable_thinking)
            if not needs_content_recovery(resp):
                return resp

            self._recovery.empty_triggers += 1

            retry_opts = ExaoneGenerateOptions(
                max_new_tokens=opts.max_new_tokens,
                temperature=opts.temperature,
                top_p=opts.top_p,
                do_sample=opts.do_sample,
                enable_thinking=False,
                tools=opts.tools,
                response_format=getattr(opts, "response_format", None),
            )
            retry = self._execute_chat_http(messages, retry_opts)
            log_llm_response_quality(
                retry, phase="thinking_off_retry", enable_thinking=False
            )
            if not needs_content_recovery(retry):
                self._recovery.recovery_successes += 1
                log_llm_response_quality(
                    retry, phase="thinking_off_retry", enable_thinking=False, recovered=True
                )
                return retry

            nudge_messages = list(messages) + [
                ExaoneMessage(role="user", content=EMPTY_CONTENT_NUDGE),
            ]
            nudge = self._execute_chat_http(nudge_messages, retry_opts)
            log_llm_response_quality(nudge, phase="nudge_retry", enable_thinking=False)
            if not needs_content_recovery(nudge):
                self._recovery.recovery_successes += 1
                log_llm_response_quality(
                    nudge, phase="nudge_retry", enable_thinking=False, recovered=True
                )
            return nudge

    return EvalRecoveryTrackingClient(
        base_url=base_url or os.environ.get("EXAONE_BASE_URL", "http://localhost:8000/v1"),
        model=model or os.environ.get("EXAONE_MODEL"),
        api_key=api_key or os.environ.get("EXAONE_API_KEY"),
    )


def read_llm_recovery_stats(llm: Any) -> RecoveryCounters:
    """
    (en) Read recovery counters from ``EvalRecoveryTrackingClient`` or ``_UsageTrackingLLM``.

    (kr) ``EvalRecoveryTrackingClient`` 또는 ``_UsageTrackingLLM``에서 recovery 카운터 읽기.
    """
    stats = getattr(llm, "recovery_stats", None)
    if stats is None:
        inner = getattr(llm, "_inner", None)
        stats = getattr(inner, "recovery_stats", None)
    if stats is None:
        return RecoveryCounters()
    if isinstance(stats, RecoveryCounters):
        return RecoveryCounters(
            empty_triggers=int(stats.empty_triggers),
            recovery_successes=int(stats.recovery_successes),
        )
    return RecoveryCounters(
        empty_triggers=int(getattr(stats, "empty_triggers", 0) or 0),
        recovery_successes=int(getattr(stats, "recovery_successes", 0) or 0),
    )


def reset_llm_recovery_stats(llm: Any) -> None:
    """
    (en) Reset recovery counters on the underlying client before each trial.

    (kr) trial마다 underlying client의 recovery 카운터를 초기화.
    """
    for target in (llm, getattr(llm, "_inner", None)):
        if target is not None and hasattr(target, "reset_recovery_stats"):
            target.reset_recovery_stats()


__all__ = [
    "RecoveryCounters",
    "make_recovery_tracking_client",
    "naive_response_needs_recovery",
    "read_llm_recovery_stats",
    "reset_llm_recovery_stats",
]
