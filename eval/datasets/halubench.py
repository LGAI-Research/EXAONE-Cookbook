"""
(en) Loader for HaluBench (`PatronusAI/HaluBench`) — a reference-free
faithfulness benchmark used to drive M9 (groundedness). HF row schema::

    {
      "id": str,           # uuid
      "passage": str,      # grounding context the answer must be entailed by
      "question": str,     # user question over the passage
      "answer": str,       # candidate answer (may be hallucinated)
      "label": "PASS"|"FAIL",  # gold faithfulness label
      "source_ds": str,    # upstream sub-dataset (DROP, PubMedQA, ...)
    }

We map each row to ``EvalTask`` with ``grounding_context=passage``,
``query=question``, and ``expected_answer={"answer": answer, "label": label}``
so a judge (RAGAS-style or HaluBench Lynx-style) can later score entailment.
Note: HaluBench gives the *candidate* answer + a binary label, so models can be
evaluated in two modes — (a) classify the given (question, answer, passage)
triple as faithful or hallucinated (zero-generation), or (b) generate an
answer over the passage and have an LLM judge score it. Both modes have access
to the same fields here.

(kr) HaluBench(`PatronusAI/HaluBench`) 로더이다. M9(groundedness) 지표를 위한 reference-free 신뢰성 벤치마크이다.
각 row를 ``EvalTask``로 매핑하며, ``grounding_context=passage``, ``query=question``,
``expected_answer={"answer": answer, "label": label}``로 둔다.
HaluBench는 후보 답변 + 이진 라벨을 제공하므로 (a) 분류 모드, (b) 생성 후 judge 채점 모드 모두에 사용 가능하다.
"""
from __future__ import annotations

import logging

from .schema import EvalTask

logger = logging.getLogger(__name__)

HALUBENCH_REPO_ID = "PatronusAI/HaluBench"
HALUBENCH_SPLIT = "test"


def load(limit: int | None = None) -> list[EvalTask]:
    """
    (en) Load HaluBench as ``EvalTask`` records. Uses streaming so a small
    ``limit`` avoids downloading the full corpus (~15k rows).

    (kr) HaluBench를 ``EvalTask`` 리스트로 로드한다.
    스트리밍을 사용하므로 ``limit`` 사용 시 전체 코퍼스(~15k row) 다운로드를 피한다.
    """
    try:
        from datasets import load_dataset as _hf_load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "datasets is required to load HaluBench; install with `pip install datasets`."
        ) from exc

    from ._cache import ensure_dataset_cache, hf_datasets_cache_dir

    ensure_dataset_cache()
    stream = _hf_load_dataset(
        HALUBENCH_REPO_ID,
        split=HALUBENCH_SPLIT,
        streaming=True,
        cache_dir=str(hf_datasets_cache_dir()),
    )

    tasks: list[EvalTask] = []
    for row in stream:
        row_id = row.get("id") or f"halubench_{len(tasks)}"
        tasks.append(
            EvalTask(
                task_id=str(row_id),
                dataset="halubench",
                category=str(row.get("source_ds") or "unknown"),
                query=row.get("question", ""),
                grounding_context=row.get("passage", ""),
                expected_answer={
                    "answer": row.get("answer"),
                    "label": row.get("label"),
                },
                metadata={
                    "halubench_source_ds": row.get("source_ds"),
                },
            )
        )
        if limit is not None and len(tasks) >= limit:
            break

    return tasks


__all__ = ["load", "HALUBENCH_REPO_ID", "HALUBENCH_SPLIT"]
