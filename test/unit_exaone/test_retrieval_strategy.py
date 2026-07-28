"""Tests for retrieval strategy configuration (fail-fast without backend wiring)."""
from __future__ import annotations

import pytest


from exaone.retrieval import (
    GraphRetrievalStrategy,
    HybridRetrievalStrategy,
    RetrievalNotConfiguredError,
    VectorRetrievalStrategy,
)


class TestVectorRetrievalStrategyConfiguration:
    def test_raises_without_embed_fn(self):
        with pytest.raises(RetrievalNotConfiguredError, match="embed_fn and search_fn"):
            VectorRetrievalStrategy(search_fn=lambda _v, _k: [])

    def test_raises_without_search_fn(self):
        with pytest.raises(RetrievalNotConfiguredError, match="embed_fn and search_fn"):
            VectorRetrievalStrategy(embed_fn=lambda _t: [0.0])

    def test_raises_with_no_args(self):
        with pytest.raises(RetrievalNotConfiguredError):
            VectorRetrievalStrategy()

    def test_allow_unconfigured_returns_empty(self):
        strategy = VectorRetrievalStrategy(allow_unconfigured=True)
        assert strategy.retrieve("query", top_k=3) == []

    def test_wired_callbacks_return_hits(self):
        strategy = VectorRetrievalStrategy(
            embed_fn=lambda text: [float(len(text))],
            search_fn=lambda vector, top_k: [
                {"text": "hit", "score": 0.9, "metadata": {"vector": vector}},
            ],
        )
        hits = strategy.retrieve("hello", top_k=1)
        assert len(hits) == 1
        assert hits[0].text == "hit"


class TestGraphRetrievalStrategyConfiguration:
    def test_raises_without_query_fn(self):
        with pytest.raises(RetrievalNotConfiguredError, match="query_fn"):
            GraphRetrievalStrategy()

    def test_allow_unconfigured_returns_empty(self):
        strategy = GraphRetrievalStrategy(allow_unconfigured=True)
        assert strategy.retrieve("query", top_k=3) == []

    def test_wired_query_fn_returns_hits(self):
        strategy = GraphRetrievalStrategy(
            query_fn=lambda q, k: [{"text": f"{q}:{k}", "score": 1.0}],
        )
        hits = strategy.retrieve("q", top_k=2)
        assert hits[0].text == "q:2"


class TestHybridRetrievalStrategyConfiguration:
    def test_raises_without_vector_strategy(self):
        graph = GraphRetrievalStrategy(query_fn=lambda q, k: [])
        with pytest.raises(RetrievalNotConfiguredError, match="vector_strategy and graph_strategy"):
            HybridRetrievalStrategy(graph_strategy=graph)

    def test_raises_without_graph_strategy(self):
        vector = VectorRetrievalStrategy(
            embed_fn=lambda _t: [0.0],
            search_fn=lambda _v, _k: [],
        )
        with pytest.raises(RetrievalNotConfiguredError):
            HybridRetrievalStrategy(vector_strategy=vector)

    def test_raises_with_no_args(self):
        with pytest.raises(RetrievalNotConfiguredError):
            HybridRetrievalStrategy()
