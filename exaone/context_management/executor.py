"""
(en) Token estimation and LLM summarization compression; used by the `messages` module.

(kr) 토큰 추정·LLM 요약 압축 모듈이며 `messages` 모듈에서 사용한다.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

from exaone.context_management.constants import (
    CONTEXT_LENGTH_RECOMMENDED_TOKENS,
    CHARS_PER_TOKEN_ESTIMATE,
)


def estimate_tokens_from_text(text: str) -> int:
    """
    (en) Estimate token count with tiktoken; fall back to character-based estimate on failure.

    (kr) tiktoken 기반으로 토큰 수를 추정하며 실패 시 문자 기반 추정으로 폴백한다.
    """
    if not text:
        return 0
    try:
        return len(_get_tiktoken_encoding().encode(text))
    except Exception:
        return max(0, (len(text) + CHARS_PER_TOKEN_ESTIMATE - 1) // CHARS_PER_TOKEN_ESTIMATE)


@lru_cache(maxsize=1)
def _get_tiktoken_encoding():
    """
    (en) Use cl100k_base by default when no EXAONE-specific tokenizer is available.

    (kr) EXAONE 전용 토크나이저가 없을 때 cl100k_base를 기본으로 사용한다.
    """
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")


def _compress_with_llm(
    content: str,
    llm: Any,
    target_max_tokens: int = CONTEXT_LENGTH_RECOMMENDED_TOKENS,
    input_max_chars: int | None = None,
) -> tuple[str, int]:
    """
    (en) Summarize content with an LLM so it fits within target_max_tokens.
    If content is too long, only the first input_max_chars are sent (avoids exceeding model context).
    Returns (compressed_text, estimated_tokens). On LLM failure returns ("", 0) — compression skipped (best-effort).

    (kr) LLM으로 content를 요약해 target_max_tokens 이하가 되도록 압축한다.
    content가 너무 길면 input_max_chars만큼만 잘라 요약 요청한다(모델 context 초과 방지).
    (compressed_text, estimated_tokens)를 반환하며 LLM 호출 실패 시 ("", 0)으로 압축을 생략한다(best-effort).
    """
    from exaone.llm import ExaoneMessage, ExaoneGenerateOptions

    if input_max_chars is None:
        input_max_chars = min(len(content), target_max_tokens * CHARS_PER_TOKEN_ESTIMATE)
    to_summarize = content[:input_max_chars] if len(content) > input_max_chars else content
    if not to_summarize.strip():
        return "", 0

    system = (
        f"You are a summarizer. Summarize the following context so that the result fits within "
        f"approximately {target_max_tokens} tokens (preserve key facts, conclusions, and decisions). "
        "Output only the summarized text, no meta-commentary."
    )
    messages = [
        ExaoneMessage(role="system", content=system),
        ExaoneMessage(role="user", content=to_summarize),
    ]
    opts = ExaoneGenerateOptions(
        max_new_tokens=min(8192, target_max_tokens),
        enable_thinking=False,
    )
    try:
        resp = llm.chat(messages, options=opts)
    except Exception:
        logger.warning("Context compression LLM call failed; skipping compression", exc_info=True)
        return "", 0
    compressed = (resp.content or "").strip()
    estimated = estimate_tokens_from_text(compressed)
    return compressed, estimated
