"""Tests for spaCy NER model preflight (graph RAG)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SPACY_MODEL = _ROOT / "infrastructure" / "ingestion" / "spacy_model.py"
_spec = importlib.util.spec_from_file_location("spacy_model", _SPACY_MODEL)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)


def test_ensure_skips_download_when_package_present(monkeypatch):
    monkeypatch.setattr(_mod.spacy.util, "is_package", lambda _m: True)
    calls: list[str] = []

    def _fail(_model: str) -> None:
        calls.append(_model)
        raise AssertionError("download should not run")

    monkeypatch.setattr(_mod, "_spacy_download", _fail)
    _mod.ensure_spacy_ner_model("xx_ent_wiki_sm")
    assert calls == []


def test_ensure_downloads_when_package_missing(monkeypatch):
    seen: list[bool] = []

    def _is_package(_model: str) -> bool:
        seen.append(True)
        return len(seen) > 1

    monkeypatch.setattr(_mod.spacy.util, "is_package", _is_package)
    downloaded: list[str] = []
    monkeypatch.setattr(_mod, "_spacy_download", lambda m: downloaded.append(m))

    _mod.ensure_spacy_ner_model("xx_ent_wiki_sm")
    assert downloaded == ["xx_ent_wiki_sm"]
