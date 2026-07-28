"""
(en) Context length management and untrusted-text sanitization.
Budget is ``input + reserved_new_tokens`` — 128k recommended, 256k hard cap.
Agents and notebooks use ensure_input_within_limit, compress_messages_for_turn, etc.

(kr) 컨텍스트 길이 관리·비신뢰 텍스트 sanitize 패키지이다.
``input + reserved_new_tokens`` 기준이며 128k 권장, 256k 상한이다.
에이전트·노트북은 ensure_input_within_limit, compress_messages_for_turn 등을 사용한다.
"""
from exaone.context_management.constants import (
    CONTEXT_LENGTH_MAX_TOKENS,
    CONTEXT_LENGTH_RECOMMENDED_TOKENS,
    CHARS_PER_TOKEN_ESTIMATE,
)
from exaone.context_management.budget import (
    hard_cap_messages,
    prepare_messages_for_llm_chat,
)
from exaone.context_management.messages import (
    message_role,
    split_leading_system,
    messages_to_text,
    estimate_tokens_from_messages,
    max_input_tokens_for_context,
    validate_input_tokens,
    cap_max_new_tokens,
    compress_messages_for_turn,
    ensure_input_within_limit,
)
from exaone.context_management.untrusted_text import sanitize_untrusted_reference_text

__all__ = [
    "CONTEXT_LENGTH_MAX_TOKENS",
    "CONTEXT_LENGTH_RECOMMENDED_TOKENS",
    "CHARS_PER_TOKEN_ESTIMATE",
    "message_role",
    "split_leading_system",
    "messages_to_text",
    "estimate_tokens_from_messages",
    "max_input_tokens_for_context",
    "validate_input_tokens",
    "cap_max_new_tokens",
    "compress_messages_for_turn",
    "ensure_input_within_limit",
    "hard_cap_messages",
    "prepare_messages_for_llm_chat",
    "sanitize_untrusted_reference_text",
]
