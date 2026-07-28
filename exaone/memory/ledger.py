"""
(en) In-memory Ledger: accumulates events and artifact references (UUID + hint) only. When `max_entries` is exceeded, `collections.deque(maxlen=...)` drops the oldest entries (keeps recent). Reads (`__iter__`, `as_list`, `last`) return independent snapshots without exposing the internal deque; mutate records only via `append`.

(kr) 인메모리 Ledger이다. 이벤트·artifact 참조(UUID + hint)만 적재한다. `max_entries`를 넘기면 `collections.deque(maxlen=...)`로 가장 오래된 항목이 자동으로 제거된다(최신 위주로 유지). 조회(`__iter__`, `as_list`, `last`)는 내부 deque를 직접 노출하지 않고 독립 스냅샷을 반환한다. 기록 변경은 `append`만 사용한다.
"""
from __future__ import annotations

import time
import uuid
from collections import deque
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

from exaone.memory.types import LedgerEntry, freeze_meta


class InMemoryLedger:
    def __init__(self, max_entries: int = 10_000) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        self._max_entries = max_entries
        self._entries: deque[LedgerEntry] = deque(maxlen=max_entries)

    @property
    def max_entries(self) -> int:
        return self._max_entries

    def __len__(self) -> int:
        return len(self._entries)

    def append(
        self,
        *,
        event_type: str,
        hint: str,
        artifact_id: str | None = None,
        meta: dict[str, Any] | None = None,
        entry_id: str | None = None,
    ) -> str:
        """
        (en) Append one row; `hint` is a short summary for model prompts. Returns entry id.

        (kr) 한 줄을 append한다. `hint`는 짧은 요약(모델에 넣을 프롬프트 힌트)용이다. entry id를 반환한다.
        """
        eid = entry_id or str(uuid.uuid4())
        self._entries.append(
            LedgerEntry(
                id=eid,
                created_at=time.time(),
                event_type=event_type,
                hint=hint,
                artifact_id=artifact_id,
                meta=freeze_meta(meta),
            )
        )
        return eid

    @staticmethod
    def _snapshot_entry(entry: LedgerEntry) -> LedgerEntry:
        return replace(entry, meta=dict(entry.meta))

    def __iter__(self) -> Iterator[LedgerEntry]:
        return (self._snapshot_entry(e) for e in self._entries)

    def as_list(self) -> list[LedgerEntry]:
        return [self._snapshot_entry(e) for e in self._entries]

    def last(self) -> LedgerEntry | None:
        if not self._entries:
            return None
        return self._snapshot_entry(self._entries[-1])
