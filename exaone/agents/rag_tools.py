"""
(en) ToolAgent (rag) tools: retrieval runs inside tool executors (no eager retrieve in run()).

Register on a ToolRegistry, then merge via ToolAgentCatalog (qualified: rag.retrieve).

(kr) ToolAgent(rag) 도구입니다. 검색은 tool executor 내부에서 실행되며(run()에서 선행 retrieve 없음),
ToolRegistry에 등록한 뒤 ToolAgentCatalog로 병합합니다(qualified: rag.retrieve).
"""
from __future__ import annotations

import logging
from typing import Any

from exaone.agents.rag_context import format_retrieved_chunks
from exaone.config import get_default_max_context_chars
from exaone.agents.tool_agent_catalog import RAG_TOOL_AGENT_KEY
from exaone.tools import ToolRegistry, tool_failure_payload, tool_from_callable

logger = logging.getLogger(__name__)

RAG_TOOL_RETRIEVE = "retrieve"
# (en) Backward-compatible aliases
# (kr) 하위 호환용 별칭
RAG_EXPERT_KEY = RAG_TOOL_AGENT_KEY

_DEFAULT_TOP_K = 5


def register_rag_tools(
    registry: ToolRegistry,
    retrieval_strategy: Any,
    *,
    max_context_chars: int | None = None,
    default_top_k: int = _DEFAULT_TOP_K,
) -> None:
    """(en) Register rag.retrieve on *registry* (qualified as rag.retrieve when merged).

    (kr) *registry*에 rag.retrieve를 등록합니다(병합 시 qualified 이름은 rag.retrieve).
    """
    if retrieval_strategy is None:
        raise ValueError("retrieval_strategy is required for rag tools")
    cap = max_context_chars if max_context_chars is not None else get_default_max_context_chars()

    def _exec_retrieve(_name: str, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "").strip()
        if not query:
            return tool_failure_payload("query is required for retrieve")
        top_k = int(args.get("top_k") or default_top_k)
        top_k = max(1, min(top_k, 20))
        try:
            chunks = retrieval_strategy.retrieve(query, top_k=top_k)
        # (en) noqa: BLE001 — retrieval backends may raise diverse transport/parse errors.
        # (kr) noqa: BLE001 — retrieval 백엔드가 다양한 transport/parse 예외를 낼 수 있다.
        # noqa: BLE001
        except Exception as exc:
            logger.exception("rag.retrieve failed")
            return tool_failure_payload(str(exc))
        if not chunks:
            return {
                "ok": True,
                "content": "[No retrieval hits]",
                "chunk_count": 0,
            }
        block = format_retrieved_chunks(chunks[:top_k], max_chars=cap)
        return {
            "ok": True,
            "content": block,
            "chunk_count": len(chunks[:top_k]),
        }

    schema = {
        "type": "function",
        "function": {
            "name": RAG_TOOL_RETRIEVE,
            "description": (
                "Retrieve document passages for the query from the configured vector/graph index. "
                "Returns numbered <chunk> blocks to use as evidence before answering."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {
                        "type": "integer",
                        "description": "Max passages to retrieve (default 5)",
                    },
                },
                "required": ["query"],
            },
        },
    }
    registry.register(tool_from_callable(RAG_TOOL_RETRIEVE, schema, _exec_retrieve))


def build_rag_tool_registry(
    retrieval_strategy: Any,
    *,
    max_context_chars: int | None = None,
    default_top_k: int = _DEFAULT_TOP_K,
) -> ToolRegistry:
    """(en) Convenience: new registry with rag.retrieve registered.

    (kr) 편의 함수입니다. rag.retrieve가 등록된 새 ToolRegistry를 반환합니다.
    """
    reg = ToolRegistry()
    register_rag_tools(
        reg,
        retrieval_strategy,
        max_context_chars=max_context_chars,
        default_top_k=default_top_k,
    )
    return reg
