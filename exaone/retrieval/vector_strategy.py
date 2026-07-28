"""
(en) Vector-based retrieval strategy.
Embedding and vector DB are injected externally so core has no DB dependency.

(kr) 벡터 기반 검색 전략이다.
임베딩/벡터 DB는 외부 주입하여 core는 DB 의존이 없다.
"""
from __future__ import annotations

from typing import Any, Callable

from exaone.retrieval.base_strategy import BaseRetrievalStrategy, RetrievalResult
from exaone.retrieval.errors import RetrievalNotConfiguredError

_VECTOR_WIRING_HINT = (
    "VectorRetrievalStrategy requires embed_fn and search_fn. "
    "Wire PgVectorAdapter from infrastructure "
    "(embed_fn_for_exaone, search_fn_for_exaone). "
    "See recipes/track04_rag_and_knowledge/ and exaone.agents.rag_tools."
)


class VectorRetrievalStrategy(BaseRetrievalStrategy):
    """
    (en) Vector similarity search. Requires injected embed_fn and search_fn.

    (kr) 벡터 유사도 검색이다. embed_fn과 search_fn을 주입한다.
    """

    def __init__(
        self,
        embed_fn: Callable[[str], list[float]] | None = None,
        search_fn: Callable[[list[float], int], list[dict[str, Any]]] | None = None,
        *,
        allow_unconfigured: bool = False,
    ):
        if not allow_unconfigured:
            if embed_fn is None or search_fn is None:
                raise RetrievalNotConfiguredError(_VECTOR_WIRING_HINT)
        self.embed_fn = embed_fn or _dummy_embed
        self.search_fn = search_fn or _dummy_search

    def retrieve(self, query: str, top_k: int = 5, **kwargs: Any) -> list[RetrievalResult]:
        vector = self.embed_fn(query)
        hits = self.search_fn(vector, top_k)
        return [
            RetrievalResult(
                text=h.get("text", h.get("content", "")),
                score=float(h.get("score", 0.0)),
                metadata=h.get("metadata"),
            )
            for h in hits
        ]


def _dummy_embed(text: str) -> list[float]:
    return [0.0] * 8


def _dummy_search(vector: list[float], top_k: int) -> list[dict[str, Any]]:
    return []
