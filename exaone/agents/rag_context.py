"""
(en) RAG retrieval context formatting and prompt-injection hardening.

Chunks from vector/graph search are untrusted third-party text. This module
wraps each chunk in <chunk> markers and strips structural tokens that could
break out of <retrieved_context> or mimic user/system turns.

(kr) RAG 검색 context 포맷팅 및 prompt-injection 방어 모듈입니다.

vector/graph 검색 청크는 신뢰할 수 없는 제3자 텍스트입니다. 이 모듈은 각 청크를
<chunk> 마커로 감싸고, <retrieved_context>를 탈출하거나 user/system 턴을 흉내 낼 수 있는
구조 토큰을 제거합니다.
"""
from __future__ import annotations

from typing import Any, Sequence

from exaone.context_management import sanitize_untrusted_reference_text

RAG_CHUNK_TAG_OPEN = "<chunk"
RAG_CHUNK_TAG_CLOSE = "</chunk>"


def _escape_xml_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _chunk_text(item: Any) -> str:
    if hasattr(item, "text"):
        return str(getattr(item, "text") or "")
    if isinstance(item, dict):
        return str(item.get("text") or item.get("content") or "")
    return str(item)


def _chunk_source(item: Any) -> str | None:
    meta: dict[str, Any] | None = None
    if hasattr(item, "metadata"):
        meta = getattr(item, "metadata", None)
    elif isinstance(item, dict):
        meta = item.get("metadata")
    if isinstance(meta, dict):
        src = meta.get("source") or meta.get("_source")
        if src is not None:
            return str(src)
    if isinstance(item, dict) and item.get("_source") is not None:
        return str(item["_source"])
    return None


def format_retrieved_chunks(
    chunks: Sequence[Any],
    *,
    max_chars: int,
    max_chunk_chars: int = 2000,
) -> str:
    """(en) Format retrieval hits as numbered <chunk> blocks for format_rag_user_message.

    (kr) 검색 hit을 format_rag_user_message용 번호가 매긴 <chunk> 블록으로 포맷합니다.
    """
    parts: list[str] = []
    for i, item in enumerate(chunks, start=1):
        raw = _chunk_text(item)[:max_chunk_chars]
        text = sanitize_untrusted_reference_text(raw)
        source = _chunk_source(item)
        if source:
            open_tag = f'<chunk index="{i}" source="{_escape_xml_attr(source)}">'
        else:
            open_tag = f'<chunk index="{i}">'
        parts.append(f"{open_tag}\n{text}\n{RAG_CHUNK_TAG_CLOSE}")
    return "\n\n".join(parts)[:max_chars]


def format_retrieved_context_from_strings(
    contexts: list[str],
    indices: list[int] | None = None,
    *,
    max_chars: int = 500_000,
    max_chunk_chars: int = 2000,
) -> str:
    """(en) Bench/eval helper: plain passage strings → ToolAgent RAG <chunk> layout.

    (kr) 벤치/eval 헬퍼입니다. 일반 passage 문자열을 ToolAgent RAG용 <chunk> 레이아웃으로 변환합니다.
    """
    if indices is None:
        indices = list(range(len(contexts)))
    chunk_dicts = [
        {"text": contexts[i], "metadata": {"source": f"passage_{i + 1}"}}
        for i in indices
    ]
    return format_retrieved_chunks(
        chunk_dicts,
        max_chars=max_chars,
        max_chunk_chars=max_chunk_chars,
    )
