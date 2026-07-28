from __future__ import annotations

import os
from dataclasses import FrozenInstanceError

from exaone.config import get_memory_artifact_max_items, get_memory_tool_result_min_bytes
from exaone.memory import InMemoryArtifactStore, InMemoryLedger, store_large_tool_result


class TestInMemoryArtifactStore:
    def test_fifo_trim_drops_oldest(self) -> None:
        s = InMemoryArtifactStore(max_items=2)
        a1 = s.put("one")
        a2 = s.put("two")
        assert set(s.snapshot_ids_ordered()) == {a1, a2}
        a3 = s.put("three")
        assert s.get(a1) is None
        assert s.get(a2) and s.get(a2).payload == "two"  # type: ignore[union-attr]
        assert s.get(a3) and s.get(a3).payload == "three"  # type: ignore[union-attr]
        assert list(s.snapshot_ids_ordered()) == [a2, a3]

    def test_get_meta_mutation_isolated(self) -> None:
        s = InMemoryArtifactStore()
        aid = s.put("data", meta={"k": 1})
        snap = s.get(aid)
        assert snap is not None
        snap.meta["k"] = 99  # type: ignore[index]
        again = s.get(aid)
        assert again is not None
        assert again.meta["k"] == 1

    def test_get_payload_mutation_isolated(self) -> None:
        s = InMemoryArtifactStore()
        aid = s.put({"a": 1})
        got = s.get(aid)
        assert got is not None
        got.payload["a"] = 2  # type: ignore[index]
        again = s.get(aid)
        assert again is not None
        assert again.payload == {"a": 1}

    def test_put_caller_mutation_isolated(self) -> None:
        s = InMemoryArtifactStore()
        original = {"nested": {"x": 1}}
        aid = s.put(original)
        original["nested"]["x"] = 99
        got = s.get(aid)
        assert got is not None
        assert got.payload == {"nested": {"x": 1}}

    def test_get_nested_mutation_isolated(self) -> None:
        s = InMemoryArtifactStore()
        aid = s.put({"nested": {"x": 1}})
        got = s.get(aid)
        assert got is not None
        got.payload["nested"]["x"] = 99  # type: ignore[index]
        again = s.get(aid)
        assert again is not None
        assert again.payload == {"nested": {"x": 1}}

    def test_pop_returns_snapshot(self) -> None:
        s = InMemoryArtifactStore()
        aid = s.put({"x": 1}, meta={"n": 1})
        popped = s.pop(aid)
        assert popped is not None
        popped.meta["n"] = 99  # type: ignore[index]
        assert s.get(aid) is None

    def test_frozen_artifact_rejects_field_reassignment(self) -> None:
        s = InMemoryArtifactStore()
        aid = s.put("x")
        art = s.get(aid)
        assert art is not None
        try:
            art.hint = "y"  # type: ignore[misc]
            raise AssertionError("expected FrozenInstanceError")
        except FrozenInstanceError:
            pass


class TestInMemoryLedger:
    def test_deque_maxlen_keeps_newest(self) -> None:
        L = InMemoryLedger(max_entries=2)
        L.append(event_type="a", hint="1")
        L.append(event_type="b", hint="2")
        L.append(event_type="c", hint="3")
        assert len(L) == 2
        hints = [e.hint for e in L.as_list()]
        assert hints == ["2", "3"]

    def test_as_list_snapshot_isolated_from_internal(self) -> None:
        L = InMemoryLedger()
        L.append(event_type="a", hint="original", meta={"k": 1})
        snap = L.as_list()[0]
        snap.meta["k"] = 99  # type: ignore[index]
        internal = L.as_list()[0]
        assert internal.hint == "original"
        assert internal.meta["k"] == 1

    def test_last_returns_snapshot(self) -> None:
        L = InMemoryLedger()
        L.append(event_type="a", hint="one", meta={"n": 1})
        last = L.last()
        assert last is not None
        last.meta["n"] = 99  # type: ignore[index]
        again = L.last()
        assert again is not None
        assert again.hint == "one"
        assert again.meta["n"] == 1

    def test_frozen_entry_rejects_field_reassignment(self) -> None:
        L = InMemoryLedger()
        L.append(event_type="a", hint="x")
        entry = L.as_list()[0]
        try:
            entry.hint = "y"  # type: ignore[misc]
            raise AssertionError("expected FrozenInstanceError")
        except FrozenInstanceError:
            pass


class TestStoreLargeToolResult:
    def test_only_large_gets_artifact(self) -> None:
        a = InMemoryArtifactStore(max_items=32)
        L = InMemoryLedger()
        sm = {"x": 1}
        r1 = store_large_tool_result(
            result=sm, artifacts=a, ledger=L, min_bytes=1_000_000
        )
        assert r1 is None
        assert len(a) == 0

        big = {"k": "y" * 5_000}
        r2 = store_large_tool_result(
            result=big, artifacts=a, ledger=L, min_bytes=100, tool_name="t"
        )
        assert r2 is not None
        assert a.get(r2) is not None
        assert any(e.artifact_id == r2 for e in L)

    def test_min_bytes_defaults_from_config(self) -> None:
        a = InMemoryArtifactStore(max_items=32)
        L = InMemoryLedger()
        threshold = get_memory_tool_result_min_bytes()
        payload = "z" * (threshold + 100)
        r = store_large_tool_result(result=payload, artifacts=a, ledger=L, tool_name="x")
        assert r is not None

    def test_large_result_artifact_get_isolated(self) -> None:
        a = InMemoryArtifactStore(max_items=32)
        L = InMemoryLedger()
        big = {"k": "y" * 5_000}
        aid = store_large_tool_result(
            result=big, artifacts=a, ledger=L, min_bytes=100, tool_name="t"
        )
        assert aid is not None
        got = a.get(aid)
        assert got is not None
        got.payload["k"] = "mutated"  # type: ignore[index]
        again = a.get(aid)
        assert again is not None
        assert again.payload["k"] == "y" * 5_000  # type: ignore[index]


class TestMemoryDefaultsFromEnv:
    def test_artifact_max_reads_env(self) -> None:
        os.environ["CORE_MEMORY_ARTIFACT_MAX_ITEMS"] = "3"
        # config 모듈은 이미 로드됨 — 루트 .env setdefault 는 덮어쓰지 않으므로 직접 set 후 리로드
        import importlib

        import exaone.config as cfg

        importlib.reload(cfg)
        try:
            assert cfg.get_memory_artifact_max_items() == 3
            s = InMemoryArtifactStore(max_items=cfg.get_memory_artifact_max_items())
            assert s.max_items == 3
        finally:
            os.environ.pop("CORE_MEMORY_ARTIFACT_MAX_ITEMS", None)
            importlib.reload(cfg)
