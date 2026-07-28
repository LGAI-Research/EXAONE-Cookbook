"""
(en) Common retrieval strategy interface.
Vector, Graph, and Hybrid all implement this interface (DB/vector DB injected externally).

(kr) 검색 전략 공통 인터페이스이다.
Vector/Graph/Hybrid는 모두 이 인터페이스를 구현한다(DB/벡터DB는 외부 주입).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievalResult:
    """
    (en) A single retrieved chunk.

    (kr) 단일 검색 결과 청크이다.
    """
    text: str
    score: float = 0.0
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"text": self.text, "score": self.score}
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    # (en) Backward-compatible accessor for legacy dict-style usages
    # (kr) 하위 호환용 접근자(레거시 dict 스타일 사용)
    def get(self, key: str, default: Any = None) -> Any:
        if key in ("text", "content"):
            return self.text
        if key == "score":
            return self.score
        if key == "metadata":
            return self.metadata
        if key == "_source":
            return (self.metadata or {}).get("_source", default)
        return default


class BaseRetrievalStrategy(ABC):
    """
    (en) Retrieval Strategy interface. Concrete storage is injected in implementations.

    (kr) Retrieval Strategy 인터페이스이다. 실제 저장소는 구현체에서 주입한다.
    """

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5, **kwargs: Any) -> list[RetrievalResult]:
        """
        (en) Retrieve top_k chunks for query. Returns a list of RetrievalResult.

        (kr) query로 top_k개 청크를 검색한다. 반환은 RetrievalResult 리스트이다.
        """
        ...
