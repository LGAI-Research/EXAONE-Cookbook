"""
(en) Builds default in-memory stores using `.env` / `exaone.config` values. See **CORE_MEMORY_*** keys in `exaone.config` and `.env.example`.

(kr) `.env` / `exaone.config` 값을 쓰는 기본 인메모리 store 생성이다. 환경 변수 키는 `exaone.config`와 `.env.example`의 **CORE_MEMORY_*** 를 참고한다.
"""
from __future__ import annotations

from exaone.config import (
    get_memory_artifact_max_items,
    get_memory_ledger_max_entries,
)
from exaone.memory.artifact_store import InMemoryArtifactStore
from exaone.memory.ledger import InMemoryLedger


def default_artifact_store() -> InMemoryArtifactStore:
    return InMemoryArtifactStore(max_items=get_memory_artifact_max_items())


def default_ledger() -> InMemoryLedger:
    return InMemoryLedger(max_entries=get_memory_ledger_max_entries())


def default_memory_pair() -> tuple[InMemoryArtifactStore, InMemoryLedger]:
    return default_artifact_store(), default_ledger()
