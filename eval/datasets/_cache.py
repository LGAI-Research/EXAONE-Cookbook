"""
(en) Repo-local cache for eval benchmark downloads. Files land under
``<repo>/_dataset/`` (gitignored) unless ``EVAL_DATASETS_DIR`` overrides the root.

(kr) eval 벤치마크 다운로드용 레포 로컬 캐시이다.
``EVAL_DATASETS_DIR``로 루트를 바꾸지 않으면 ``<repo>/_dataset/``(gitignore)에 저장된다.
"""
from __future__ import annotations

import os
from pathlib import Path

from eval._env import REPO_ROOT

_CACHE_CONFIGURED = False


def datasets_root() -> Path:
    """
    (en) Root directory for all eval dataset artifacts (default: ``REPO_ROOT/_dataset``).

    (kr) eval 데이터셋 아티팩트 루트 디렉터리(기본: ``REPO_ROOT/_dataset``).
    """
    override = os.environ.get("EVAL_DATASETS_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return REPO_ROOT / "_dataset"


def hub_cache_dir() -> Path:
    """
    (en) ``huggingface_hub.hf_hub_download`` cache (BFCL JSONL files).

    (kr) ``huggingface_hub.hf_hub_download`` 캐시(BFCL JSONL).
    """
    return datasets_root() / "hub"


def hf_datasets_cache_dir() -> Path:
    """
    (en) ``datasets.load_dataset`` cache (IFEval, HaluBench).

    (kr) ``datasets.load_dataset`` 캐시(IFEval, HaluBench).
    """
    return datasets_root() / "hf_datasets"


def ensure_dataset_cache() -> Path:
    """
    (en) Create cache dirs and set ``HF_HUB_CACHE`` / ``HF_DATASETS_CACHE`` via
    ``setdefault`` so an explicit env override still wins. Idempotent.

    (kr) 캐시 디렉터리를 만들고 ``HF_HUB_CACHE`` / ``HF_DATASETS_CACHE``를
    ``setdefault``로 설정한다(명시적 env가 우선). 멱등이다.
    """
    global _CACHE_CONFIGURED
    root = datasets_root()
    hub = hub_cache_dir()
    hf_ds = hf_datasets_cache_dir()
    hub.mkdir(parents=True, exist_ok=True)
    hf_ds.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HUB_CACHE", str(hub))
    os.environ.setdefault("HF_DATASETS_CACHE", str(hf_ds))
    _CACHE_CONFIGURED = True
    return root


__all__ = [
    "datasets_root",
    "hub_cache_dir",
    "hf_datasets_cache_dir",
    "ensure_dataset_cache",
]
