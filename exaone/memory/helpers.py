"""
(en) Helpers linking tool responses to Artifact / Ledger. Large responses go only into artifact; ledger keeps `artifact_id` + `hint`. Small responses may use ledger only (optional) or skip both.

(kr) 도구 응답을 Artifact / Ledger에 연결하는 보조 함수이다. 큰 응답은 artifact에만 넣고 ledger에는 `artifact_id` + `hint`만 남긴다. 작은 응답은 artifact 없이 ledger만 쓰거나(선택), 둘 다 쓰지 않을 수 있다.
"""
from __future__ import annotations

import json
from typing import Any

from exaone.config import get_memory_tool_result_min_bytes
from exaone.memory.artifact_store import InMemoryArtifactStore
from exaone.memory.ledger import InMemoryLedger


def _approx_serialized_size_bytes(obj: Any) -> int:
    if obj is None:
        return 0
    if isinstance(obj, (bytes, bytearray)):
        return len(obj)
    if isinstance(obj, str):
        return len(obj.encode("utf-8", errors="replace"))
    try:
        return len(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))
    except TypeError:
        return len(repr(obj).encode("utf-8", errors="replace"))


def store_large_tool_result(
    *,
    result: Any,
    artifacts: InMemoryArtifactStore,
    ledger: InMemoryLedger,
    event_type: str = "tool_result",
    min_bytes: int | None = None,
    tool_name: str = "",
) -> str | None:
    """
    (en) If serialized size of `result` is at least `min_bytes`, store in artifact and leave a ref on ledger. When `min_bytes` is None, uses `.env` `CORE_MEMORY_TOOL_RESULT_MIN_BYTES` / `exaone.config.get_memory_tool_result_min_bytes()`. Returns artifact id, or None if not stored.

    (kr) `result`의 직렬화 크기가 `min_bytes` 이상이면 artifact에 넣고 ledger에 ref를 남긴다. `min_bytes`가 None이면 `.env`의 `CORE_MEMORY_TOOL_RESULT_MIN_BYTES` / `exaone.config.get_memory_tool_result_min_bytes()`를 쓴다. artifact id를 반환하며, 스토어에 넣지 않으면 None을 반환한다.
    """
    threshold = min_bytes if min_bytes is not None else get_memory_tool_result_min_bytes()
    size = _approx_serialized_size_bytes(result)
    if size < threshold:
        return None
    meta = {"tool": tool_name, "approx_bytes": size} if tool_name else {"approx_bytes": size}
    aid = artifacts.put(
        result,
        hint=(tool_name or "tool") + f" · ~{size}B",
        meta=meta,
    )
    ledger.append(
        event_type=event_type,
        hint=f"artifact:{aid}",
        artifact_id=aid,
        meta=meta,
    )
    return aid
