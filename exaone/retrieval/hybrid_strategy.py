"""
(en) Combined Vector + Graph strategy.
Weighted fusion or sequential application (selectable via configuration).

(kr) Vector + Graph 결합 전략이다.
가중 합산 또는 순차 적용(설정으로 선택)한다.
"""
from __future__ import annotations

from typing import Any

from exaone.retrieval.base_strategy import BaseRetrievalStrategy, RetrievalResult
from exaone.retrieval.errors import RetrievalNotConfiguredError
from exaone.retrieval.graph_strategy import GraphRetrievalStrategy
from exaone.retrieval.vector_strategy import VectorRetrievalStrategy

_HYBRID_WIRING_HINT = (
    "HybridRetrievalStrategy requires vector_strategy and graph_strategy. "
    "Construct configured VectorRetrievalStrategy and GraphRetrievalStrategy first. "
    "See recipes/track04_rag_and_knowledge/ and exaone.integrations retrieval."
)


class HybridRetrievalStrategy(BaseRetrievalStrategy):
    """
    (en) Merges vector and graph results (RRF-based rank fusion).

    (kr) 벡터와 그래프 결과를 합쳐서 반환한다(RRF 기반 순위 결합).
    """

    def __init__(
        self,
        vector_strategy: VectorRetrievalStrategy | None = None,
        graph_strategy: GraphRetrievalStrategy | None = None,
        vector_weight: float = 0.7,
        graph_weight: float = 0.3,
    ):
        if vector_strategy is None or graph_strategy is None:
            raise RetrievalNotConfiguredError(_HYBRID_WIRING_HINT)
        self.vector_strategy = vector_strategy
        self.graph_strategy = graph_strategy
        self.vector_weight = vector_weight
        self.graph_weight = graph_weight

    def retrieve(self, query: str, top_k: int = 5, **kwargs: Any) -> list[RetrievalResult]:
        # (en) Per-strategy ordering respects each score; fusion uses rank-based RRF
        # (kr) 전략별 내부 정렬은 각 score를 존중하고, 결합은 순위 기반(RRF)으로 한다
        v_hits = sorted(
            self.vector_strategy.retrieve(query, top_k=top_k, **kwargs),
            key=lambda x: x.get("score") or 0.0,
            reverse=True,
        )
        g_hits = sorted(
            self.graph_strategy.retrieve(query, top_k=top_k, **kwargs),
            key=lambda x: x.get("score") or 0.0,
            reverse=True,
        )

        v_hits = _apply_rrf_scores(v_hits, weight=self.vector_weight)
        g_hits = _apply_rrf_scores(g_hits, weight=self.graph_weight)

        for h in v_hits:
            _with_source(h, "vector")
        for h in g_hits:
            _with_source(h, "graph")

        combined = v_hits + g_hits
        combined.sort(key=lambda x: x.get("score") or 0.0, reverse=True)

        # (en) Deduplicate by text
        # (kr) 중복 텍스트를 제거한다
        seen: set[str] = set()
        deduped: list[RetrievalResult] = []
        for h in combined:
            text_key = (h.get("text") or "")[:200]
            if text_key not in seen:
                seen.add(text_key)
                deduped.append(h)

        # (en) Ensure at least one graph hit when graph results exist
        # (kr) graph 결과가 있을 때 최소 1개는 포함되도록 한다
        result = deduped[:top_k]
        has_graph = any(h.get("_source") == "graph" for h in result)
        if not has_graph and g_hits:
            result = result[: top_k - 1] + [g_hits[0]]

        return result


def _apply_rrf_scores(
    hits: list[RetrievalResult],
    *,
    weight: float,
    rrf_k: int = 60,
) -> list[RetrievalResult]:
    """
    (en) Overwrite scores with rank-based RRF: score = weight * (1 / (rrf_k + rank)).

    (kr) 순위 기반 RRF 점수로 덮어쓴다: score = weight * (1 / (rrf_k + rank)).
    """
    for rank, hit in enumerate(hits, start=1):
        hit.score = weight * (1.0 / (rrf_k + rank))
    return hits


def _with_source(hit: RetrievalResult, source: str) -> None:
    metadata = dict(hit.metadata or {})
    metadata.setdefault("_source", source)
    hit.metadata = metadata
