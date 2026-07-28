"""
(en) Context length constants read only from root/.env via exaone.config (single source: exaone/config.py).

(kr) 컨텍스트 길이 상수 모듈이다. root/.env에서만 읽으며(exaone.config) 단일 소스는 exaone/config.py이다.
"""
from __future__ import annotations

from exaone.config import (
    get_context_length_max_tokens,
    get_context_length_recommended_tokens,
    get_chars_per_token_estimate,
    get_context_tool_verbatim_max_tokens,
)

CONTEXT_LENGTH_MAX_TOKENS = get_context_length_max_tokens()
CONTEXT_LENGTH_RECOMMENDED_TOKENS = get_context_length_recommended_tokens()
CHARS_PER_TOKEN_ESTIMATE = get_chars_per_token_estimate()
CONTEXT_TOOL_VERBATIM_MAX_TOKENS = get_context_tool_verbatim_max_tokens()

__all__ = [
    "CONTEXT_LENGTH_MAX_TOKENS",
    "CONTEXT_LENGTH_RECOMMENDED_TOKENS",
    "CHARS_PER_TOKEN_ESTIMATE",
    "CONTEXT_TOOL_VERBATIM_MAX_TOKENS",
]
