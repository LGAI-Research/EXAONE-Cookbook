"""
(en) In-memory Artifact store: large tool responses and similar payloads by ID. When capacity exceeds `max_items`, the oldest items are removed (FIFO). Ledger may still reference an old `artifact_id` after eviction, so `get` can return `None`. `put`, `get`, and `pop` deep-copy `dict`/`list` payloads so callers cannot corrupt internal state; mutate only via `put`.

(kr) 인메모리 Artifact 저장소이다. 큰 tool 응답 등을 ID로 보관한다. 용량이 `max_items`를 넘으면 가장 오래된 항목부터 제거한다(FIFO). Ledger가 예전 `artifact_id`를 가리키는데 Artifact만 먼저 지워질 수 있으므로 `get`은 `None`을 반환할 수 있다. 저장(`put`)·조회(`get`, `pop`) 모두 `dict`/`list` `payload`는 `copy.deepcopy`로 분리하며, 기록 변경은 `put`만 사용한다.
"""
from __future__ import annotations

import copy
import time
import uuid
from collections import deque
from dataclasses import replace
from typing import Any

from exaone.memory.types import StoredArtifact, freeze_meta


def _defensive_copy_payload(payload: Any) -> Any:
    if isinstance(payload, (dict, list)):
        return copy.deepcopy(payload)
    return payload


class InMemoryArtifactStore:
    def __init__(self, max_items: int = 256) -> None:
        if max_items < 1:
            raise ValueError("max_items must be >= 1")
        self._max_items = max_items
        self._by_id: dict[str, StoredArtifact] = {}
        self._order: deque[str] = deque()

    @property
    def max_items(self) -> int:
        return self._max_items

    def __len__(self) -> int:
        return len(self._by_id)

    @staticmethod
    def _snapshot_artifact(artifact: StoredArtifact) -> StoredArtifact:
        return replace(
            artifact,
            meta=dict(artifact.meta),
            payload=_defensive_copy_payload(artifact.payload),
        )

    def put(
        self,
        payload: Any,
        *,
        hint: str = "",
        meta: dict[str, Any] | None = None,
        artifact_id: str | None = None,
    ) -> str:
        """
        (en) Store `payload` and return its ID. :param hint: short description (used with ledger). :param meta: arbitrary metadata such as tool name or turn ID. :param artifact_id: store under this UUID when given (otherwise create new).

        (kr) `payload`를 저장하고 ID를 반환한다. :param hint: 짧은 설명(ledger와 함께 쓴다). :param meta: 툴 이름, 턴 ID 등 임의 메타. :param artifact_id: 지정 시 해당 UUID로 저장한다(없으면 신규 생성).
        """
        aid = artifact_id or str(uuid.uuid4())
        now = time.time()
        st = StoredArtifact(
            id=aid,
            created_at=now,
            payload=_defensive_copy_payload(payload),
            hint=hint,
            meta=freeze_meta(meta),
        )
        if aid in self._by_id:
            # (en) Re-store: keep order, overwrite payload
            # (kr) 재저장. 순서는 그대로 두고 덮어쓴다
            self._by_id[aid] = st
        else:
            self._by_id[aid] = st
            self._order.append(aid)
        self._trim_oldest()
        return aid

    def get(self, artifact_id: str) -> StoredArtifact | None:
        stored = self._by_id.get(artifact_id)
        if stored is None:
            return None
        return self._snapshot_artifact(stored)

    def pop(self, artifact_id: str) -> StoredArtifact | None:
        got = self._by_id.pop(artifact_id, None)
        if got is None:
            return None
        try:
            self._order.remove(artifact_id)
        except ValueError:
            pass
        return self._snapshot_artifact(got)

    def _trim_oldest(self) -> None:
        while len(self._order) > self._max_items:
            old = self._order.popleft()
            self._by_id.pop(old, None)

    def snapshot_ids_ordered(self) -> list[str]:
        """
        (en) Current artifact IDs in FIFO order (for debugging and tests).

        (kr) 현재 FIFO 순서의 artifact ID 목록이다(디버깅·테스트용).
        """
        return list(self._order)
