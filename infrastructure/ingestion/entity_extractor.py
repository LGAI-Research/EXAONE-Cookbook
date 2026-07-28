"""Entity extractor for Graph RAG (spaCy NER-based, 임시 구현).

Plan (docs/LLAMAINDEX_RAG_MIGRATION_PLAN.md) 의 Phase 3 권장 구현은 LlamaIndex
`SimpleLLMPathExtractor` (LLM 호출로 트리플 추출) 이지만, 15,098 청크에 대해 LLM 을
호출하는 데 수 시간·API 비용 부담이 큼 + Phase 0/1 헬퍼 파일 미완 상태라 prereq 부재.

임시로 spaCy NER (로컬, LLM 없음, 수 분 내 전 청크 처리) 로 구현:
- 장점: LLM 비용 0, 수 분 내 완료, ingestion 종속성 최소
- 한계: 명명 엔티티만 추출 (관계는 build_rag_from_ms_marco.py 가 co-occurrence 로 대체
  생성하므로 별도 관계 추출 불필요), 도메인 특화 엔티티 약함 (의학·법률 등은 NER
  표준 태그에 묶임)
- 향후 전환: Plan Phase 0/1 이 완성되면 `SimpleLLMPathExtractor` 로 교체 고려.

자세한 배경은 cookbook/rag_migration_state.md 참고.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from spacy.language import Language
except ImportError as e:
    raise ImportError(
        "spacy 가 설치되어 있지 않습니다. `pip install spacy` 후 step3 preflight 또는:\n"
        "  python -m infrastructure.ingestion.spacy_model"
    ) from e

from infrastructure.ingestion.spacy_model import DEFAULT_SPACY_NER_MODEL, load_spacy_ner_model


@dataclass
class Entity:
    """추출된 엔티티. build_rag_from_ms_marco.py 가 기대하는 최소 속성."""

    name: str
    type: str
    description: Optional[str] = None


class EntityExtractor:
    """spaCy NER 기반 엔티티 추출기.

    Usage:
        extractor = EntityExtractor()
        for ent in extractor.extract("2024년 서울에서 LG 연구원이 발표..."):
            print(ent.name, ent.type)   # 서울 GPE / LG 연구원 ORG / ...
    """

    def __init__(self, model: str = DEFAULT_SPACY_NER_MODEL):
        self._nlp: Language = load_spacy_ner_model(model)

    def extract(self, text: str) -> list[Entity]:
        """텍스트에서 고유 엔티티 목록 반환. 중복 (이름, 타입) 은 1회만."""
        seen: set[tuple[str, str]] = set()
        out: list[Entity] = []
        for ent in self._nlp(text).ents:
            key = (ent.text.strip(), ent.label_)
            if not key[0] or key in seen:
                continue
            seen.add(key)
            out.append(Entity(name=key[0], type=key[1]))
        return out
