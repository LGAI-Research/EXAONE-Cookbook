"""
(en) Shared types for Ledger and ArtifactStore.

(kr) Ledger·ArtifactStore 공통 타입이다.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


def freeze_meta(meta: dict[str, Any] | None) -> MappingProxyType:
    """
    (en) Read-only meta for ledger/artifact internals, isolated from the caller's dict.

    (kr) Ledger/artifact 내부용 읽기 전용 meta이다. 호출자 dict와 분리된다.
    """
    return MappingProxyType(dict(meta) if meta else {})


@dataclass(frozen=True)
class LedgerEntry:
    """
    (en) One ledger row: stores `artifact_id` plus a short `hint` instead of large body text.

    (kr) Ledger 한 줄이다. 대용량 본문 대신 `artifact_id` + 짧은 `hint`만 둔다.
    """

    id: str
    created_at: float
    event_type: str
    hint: str
    artifact_id: str | None = None
    meta: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class StoredArtifact:
    """
    (en) In-memory artifact storage unit; `payload` stays close to the original before passing to LLM/tools.

    (kr) Artifact 저장 단위(인메모리)이다. `payload`는 LLM/도구에 그대로 넘기기 전 원본에 가깝게 둔다.
    """

    id: str
    created_at: float
    payload: Any
    hint: str = ""
    meta: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
