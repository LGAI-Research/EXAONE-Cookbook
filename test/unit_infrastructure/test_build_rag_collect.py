"""Unit tests for MS MARCO context collection caps in step3."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BUILD_RAG = _ROOT / "infrastructure" / "setup" / "build_rag_from_ms_marco.py"
_spec = importlib.util.spec_from_file_location("build_rag_from_ms_marco", _BUILD_RAG)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)


def _fake_dataset(rows: list[dict]) -> dict:
    return {"train": rows}


def test_collect_contexts_dedupes_and_respects_max():
    ds = _fake_dataset(
        [
            {
                "query_id": "1",
                "passages": {
                    "passage_text": ["alpha passage", "alpha passage", "beta passage"],
                    "is_selected": [1, 0, 1],
                    "url": ["", "", "http://example.com"],
                },
            },
            {
                "query_id": "2",
                "passages": {
                    "passage_text": ["gamma passage"],
                    "is_selected": [0],
                    "url": [""],
                },
            },
        ]
    )

    all_ctx = _mod.collect_contexts(ds)
    assert len(all_ctx) == 3

    capped = _mod.collect_contexts(ds, max_contexts=2)
    assert len(capped) == 2
    assert capped[0][0] == "alpha passage"
    assert capped[1][0] == "beta passage"


def test_env_positive_int_or_none():
    import os

    key = "STEP3_MAX_CONTEXTS_TEST"
    os.environ.pop(key, None)
    assert _mod._env_positive_int_or_none(key) is None

    os.environ[key] = "0"
    assert _mod._env_positive_int_or_none(key) is None

    os.environ[key] = "5000"
    assert _mod._env_positive_int_or_none(key) == 5000

    os.environ.pop(key, None)
