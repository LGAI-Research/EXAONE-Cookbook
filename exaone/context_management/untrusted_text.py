"""
(en) Sanitize untrusted text before embedding in LLM prompts (RAG chunks, tool results).

(kr) LLM 프롬프트에 넣기 전 비신뢰 텍스트를 정제한다(RAG chunk, tool 결과).
"""
from __future__ import annotations

import re

_RE_RETRIEVED_CONTEXT = re.compile(r"</?\s*retrieved_context\s*/?>", re.IGNORECASE)
_RE_CHUNK_TAG = re.compile(r"</?\s*chunk(?:\s[^>]*)?>", re.IGNORECASE)
_RE_TOOL_RESULT_TAG = re.compile(r"</?\s*tool_result(?:\s[^>]*)?>", re.IGNORECASE)
_RE_QUESTION_LINE = re.compile(r"(?m)^(Question:\s*)")


def sanitize_untrusted_reference_text(text: str) -> str:
    """
    (en) Neutralize delimiter and instruction-mimic patterns in untrusted text.

    (kr) 비신뢰 텍스트의 구분자·지시문 모방 패턴을 무력화한다.
    """
    if not text:
        return text
    out = _RE_RETRIEVED_CONTEXT.sub("[removed-tag:retrieved_context]", text)
    out = _RE_CHUNK_TAG.sub("[removed-tag:chunk]", out)
    out = _RE_TOOL_RESULT_TAG.sub("[removed-tag:tool_result]", out)
    out = _RE_QUESTION_LINE.sub(r"[ref] \1", out)
    return out
