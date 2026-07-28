"""
(en) Unit tests for repo-local ``_dataset/`` cache paths.

(kr) 레포 로컬 ``_dataset/`` 캐시 경로 단위 테스트.
"""
from __future__ import annotations

import os

import pytest

from eval.datasets._cache import (
    datasets_root,
    ensure_dataset_cache,
    hf_datasets_cache_dir,
    hub_cache_dir,
)


def test_datasets_root_defaults_to_repo_dataset_dir(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.delenv("EVAL_DATASETS_DIR", raising=False)
    monkeypatch.setattr("eval.datasets._cache.REPO_ROOT", tmp_path)
    assert datasets_root() == tmp_path / "_dataset"


def test_datasets_root_honors_eval_datasets_dir(monkeypatch: pytest.MonkeyPatch, tmp_path):
    custom = tmp_path / "my_cache"
    monkeypatch.setenv("EVAL_DATASETS_DIR", str(custom))
    assert datasets_root() == custom.resolve()


def test_ensure_dataset_cache_creates_hub_and_hf_subdirs(monkeypatch: pytest.MonkeyPatch, tmp_path):
    root = tmp_path / "_dataset"
    monkeypatch.setenv("EVAL_DATASETS_DIR", str(root))
    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    monkeypatch.delenv("HF_DATASETS_CACHE", raising=False)

    ensure_dataset_cache()

    assert hub_cache_dir() == root / "hub"
    assert hf_datasets_cache_dir() == root / "hf_datasets"
    assert hub_cache_dir().is_dir()
    assert hf_datasets_cache_dir().is_dir()
    assert os.environ["HF_HUB_CACHE"] == str(root / "hub")
    assert os.environ["HF_DATASETS_CACHE"] == str(root / "hf_datasets")


def test_ensure_dataset_cache_does_not_override_existing_hf_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    monkeypatch.setenv("EVAL_DATASETS_DIR", str(tmp_path / "_dataset"))
    monkeypatch.setenv("HF_HUB_CACHE", "/custom/hub")
    monkeypatch.setenv("HF_DATASETS_CACHE", "/custom/hf_datasets")

    ensure_dataset_cache()

    assert os.environ["HF_HUB_CACHE"] == "/custom/hub"
    assert os.environ["HF_DATASETS_CACHE"] == "/custom/hf_datasets"
