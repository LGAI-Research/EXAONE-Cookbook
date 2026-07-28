"""Ingestion helpers for Graph RAG (spaCy NER entity extraction)."""

from infrastructure.ingestion.entity_extractor import Entity, EntityExtractor
from infrastructure.ingestion.spacy_model import DEFAULT_SPACY_NER_MODEL, ensure_spacy_ner_model

__all__ = [
    "DEFAULT_SPACY_NER_MODEL",
    "Entity",
    "EntityExtractor",
    "ensure_spacy_ner_model",
]
