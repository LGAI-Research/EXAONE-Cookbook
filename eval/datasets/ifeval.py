"""
(en) Loader for IFEval (Google, Zhou et al. 2023 — https://arxiv.org/abs/2311.07911)
hosted at HuggingFace `google/IFEval`.

Each row carries a natural-language ``prompt`` plus the list of *verifiable
instructions* embedded in it. The HF schema is::

    {
      "key": int,                       # numeric id
      "prompt": str,                    # user-visible instruction text
      "instruction_id_list": list[str], # e.g. ["punctuation:no_comma", ...]
      "kwargs": list[dict[str, Any]],   # per-instruction argument bag (parallel index)
    }

We map each prompt to one ``EvalTask`` with ``json_schema=None`` and
``required_keys=None`` (IFEval is free-form text, not JSON). The verifiable
instruction list — paired ``id`` + ``kwargs`` so downstream M6 strict/loose
checkers (`langdetect`, regex, length, format) can replay the
instruction-following protocol — is stored under
``metadata["ifeval_instructions"]``.

(kr) IFEval(`google/IFEval`) 로더이다. 각 row는 사용자 프롬프트와 그 안에 내포된 verifiable instruction 리스트를 가진다.
프롬프트 1개당 ``EvalTask`` 1개로 매핑하며, IFEval은 JSON이 아닌 free-form 텍스트이므로 ``json_schema=None``, ``required_keys=None``이다.
M6 strict/loose 채점기가 그대로 재현할 수 있도록 (``instruction_id``, ``kwargs``) 쌍 리스트를 ``metadata["ifeval_instructions"]``에 저장한다.
"""
from __future__ import annotations

import logging
from typing import Any

from .schema import EvalTask

logger = logging.getLogger(__name__)

IFEVAL_REPO_ID = "google/IFEval"
IFEVAL_SPLIT = "train"  # IFEval ships a single split


def _pair_instructions(ids: list[str] | None, kwargs_list: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """
    (en) Zip ``instruction_id_list`` and ``kwargs`` into ``[{id, kwargs}, ...]``.
    HF rows fill missing kwargs with ``None`` per field — we strip those so the
    payload stays compact.

    (kr) ``instruction_id_list``와 ``kwargs``를 ``[{id, kwargs}, ...]`` 형태로 짝짓는다.
    HF row는 누락된 kwargs를 필드별 ``None``으로 채우므로 이를 제거해 payload를 간결하게 유지한다.
    """
    ids = ids or []
    kwargs_list = kwargs_list or []
    out: list[dict[str, Any]] = []
    for i, inst_id in enumerate(ids):
        raw = kwargs_list[i] if i < len(kwargs_list) else {}
        clean = {k: v for k, v in (raw or {}).items() if v is not None}
        out.append({"id": inst_id, "kwargs": clean})
    return out


def load(limit: int | None = None) -> list[EvalTask]:
    """
    (en) Load IFEval as a flat list of ``EvalTask``. Streams the HF split so
    ``limit`` does not force a full download of the (~500 row) corpus.

    (kr) IFEval을 ``EvalTask`` 평탄 리스트로 로드한다.
    HF split을 스트리밍하여 ``limit`` 사용 시 전체 코퍼스(~500 row)를 다운로드하지 않는다.
    """
    try:
        from datasets import load_dataset as _hf_load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "datasets is required to load IFEval; install with `pip install datasets`."
        ) from exc

    from ._cache import ensure_dataset_cache, hf_datasets_cache_dir

    ensure_dataset_cache()
    stream = _hf_load_dataset(
        IFEVAL_REPO_ID,
        split=IFEVAL_SPLIT,
        streaming=True,
        cache_dir=str(hf_datasets_cache_dir()),
    )

    tasks: list[EvalTask] = []
    for row in stream:
        ids = row.get("instruction_id_list") or []
        kwargs_list = row.get("kwargs") or []
        instructions = _pair_instructions(ids, kwargs_list)
        key = row.get("key")
        tasks.append(
            EvalTask(
                task_id=f"ifeval_{key}" if key is not None else f"ifeval_{len(tasks)}",
                dataset="ifeval",
                category="verifiable_instructions",
                query=row.get("prompt", ""),
                json_schema=None,
                required_keys=None,
                metadata={
                    "ifeval_instructions": instructions,
                    "ifeval_key": key,
                },
            )
        )
        if limit is not None and len(tasks) >= limit:
            break

    return tasks


__all__ = ["load", "IFEVAL_REPO_ID", "IFEVAL_SPLIT"]
