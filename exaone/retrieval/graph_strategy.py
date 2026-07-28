"""
(en) Relation-based retrieval strategy (graph/entity relations).
Actual graph DB is injected externally.

(kr) 관계 기반 검색 전략(그래프/엔티티 관계)이다.
실제 그래프 DB는 외부 주입한다.
"""
from __future__ import annotations

from typing import Any, Callable

from exaone.retrieval.base_strategy import BaseRetrievalStrategy, RetrievalResult
from exaone.retrieval.errors import RetrievalNotConfiguredError

_GRAPH_WIRING_HINT = (
    "GraphRetrievalStrategy requires query_fn. "
    "Wire PgGraphAdapter from infrastructure (query_fn_for_exaone). "
    "See recipes/track04_rag_and_knowledge/ and exaone.agents.rag_tools."
)


class GraphRetrievalStrategy(BaseRetrievalStrategy):
    """
    (en) Returns graph query results as document chunks. Requires injected query_fn.

    (kr) 그래프 쿼리 결과를 문서 청크 형태로 반환한다. query_fn을 주입한다.
    """

    def __init__(
        self,
        query_fn: Callable[[str, int], list[dict[str, Any]]] | None = None,
        *,
        allow_unconfigured: bool = False,
    ):
        if not allow_unconfigured and query_fn is None:
            raise RetrievalNotConfiguredError(_GRAPH_WIRING_HINT)
        self.query_fn = query_fn or _dummy_graph_query

    def retrieve(self, query: str, top_k: int = 5, **kwargs: Any) -> list[RetrievalResult]:
        hits = self.query_fn(query, top_k)
        return [
            RetrievalResult(
                text=h.get("text", h.get("content", str(h))),
                score=float(h.get("score", 0.0)),
                metadata=h.get("metadata"),
            )
            for h in hits
        ]


def _dummy_graph_query(query: str, top_k: int) -> list[dict[str, Any]]:
    return []
