"""
(en) Registry entry-point for external benchmark loaders consumed by
``eval/runners/`` and ``eval/run.py``. Each loader is provider-agnostic
and emits ``list[EvalTask]`` (see ``schema.py``).

Supported names (call ``available_datasets()`` for the live list):

- ``bfcl_v3`` — all four sub-categories concatenated.
- ``bfcl_v3.simple`` / ``bfcl_v3.multiple`` / ``bfcl_v3.parallel`` / ``bfcl_v3.irrelevance``
- ``ifeval``
- ``halubench``
- ``tau_bench`` / ``tau_bench.retail`` / ``tau_bench.airline``
  (requires optional ``eval-taubench`` install; uses ``tau_bench_runner``)

Usage::

    from eval.datasets import load_dataset
    tasks = load_dataset("bfcl_v3.simple", limit=5)

(kr) ``eval/runners/``와 ``eval/run.py``가 사용하는 외부 벤치마크 로더의 registry entry-point이다.
각 로더는 provider 비의존이며 ``list[EvalTask]``를 반환한다(``schema.py`` 참조).
"""
from __future__ import annotations

from typing import Callable

from . import bfcl_v3, halubench, ifeval, tau_bench
from ._cache import (
    datasets_root,
    ensure_dataset_cache,
    hf_datasets_cache_dir,
    hub_cache_dir,
)
from ._net import is_online
from .schema import EvalTask, ExpectedToolCall, ToolSpec

_LoaderFn = Callable[[int | None], list[EvalTask]]


def _bfcl_all(limit: int | None) -> list[EvalTask]:
    return bfcl_v3.load(category=None, limit=limit)


def _bfcl_sub(category: str) -> _LoaderFn:
    def _fn(limit: int | None) -> list[EvalTask]:
        return bfcl_v3.load(category=category, limit=limit)
    _fn.__name__ = f"_bfcl_{category}"
    return _fn


def _tau_all(limit: int | None) -> list[EvalTask]:
    return tau_bench.load(domain=None, limit=limit)


def _tau_sub(domain: str) -> _LoaderFn:
    def _fn(limit: int | None) -> list[EvalTask]:
        return tau_bench.load(domain=domain, limit=limit)
    _fn.__name__ = f"_tau_{domain}"
    return _fn


_REGISTRY: dict[str, _LoaderFn] = {
    "bfcl_v3":              _bfcl_all,
    "bfcl_v3.simple":       _bfcl_sub("simple"),
    "bfcl_v3.multiple":     _bfcl_sub("multiple"),
    "bfcl_v3.parallel":     _bfcl_sub("parallel"),
    "bfcl_v3.irrelevance":  _bfcl_sub("irrelevance"),
    "ifeval":               ifeval.load,
    "halubench":            halubench.load,
    "tau_bench":            _tau_all,
    "tau_bench.retail":     _tau_sub("retail"),
    "tau_bench.airline":    _tau_sub("airline"),
}


def available_datasets() -> list[str]:
    """
    (en) Names accepted by ``load_dataset``. Sorted for stable CLI listing.
    (kr) ``load_dataset``이 허용하는 이름 목록이다. CLI 표시 안정성을 위해 정렬한다.
    """
    return sorted(_REGISTRY.keys())


def load_dataset(name: str, limit: int | None = None) -> list[EvalTask]:
    """
    (en) Registry-style entry-point. Resolves ``name`` to the matching loader
    and returns up to ``limit`` ``EvalTask`` instances (or all if ``limit`` is None).
    Raises ``KeyError`` for unknown names — call ``available_datasets()`` to enumerate.

    (kr) registry 스타일 entry-point이다. ``name``을 해당 로더로 해석하여 최대 ``limit``개의 ``EvalTask``를 반환한다
    (``limit``이 None이면 전체). 알 수 없는 이름은 ``KeyError``를 발생시키며, ``available_datasets()``로 사용 가능한 이름을 확인할 수 있다.
    """
    try:
        loader = _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown dataset '{name}'. Available: {available_datasets()}"
        ) from exc
    ensure_dataset_cache()
    return loader(limit)


__all__ = [
    "load_dataset",
    "available_datasets",
    "is_online",
    "EvalTask",
    "ExpectedToolCall",
    "ToolSpec",
    "bfcl_v3",
    "ifeval",
    "halubench",
    "tau_bench",
    "datasets_root",
    "ensure_dataset_cache",
    "hub_cache_dir",
    "hf_datasets_cache_dir",
]
