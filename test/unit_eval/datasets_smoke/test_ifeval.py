"""
(en) Online smoke test for `eval.datasets.ifeval`. Verifies ≥1 task is
returned and the verifiable-instruction list is non-empty for each task.

(kr) `eval.datasets.ifeval` 온라인 스모크 테스트이다.
>=1개 태스크가 반환되고 각 태스크의 verifiable-instruction 리스트가 비어있지 않은지 검증한다.
"""
from __future__ import annotations

import pytest

from eval.datasets import load_dataset
from eval.datasets._net import is_online

pytestmark = pytest.mark.eval_datasets


@pytest.mark.skipif(not is_online(), reason="HuggingFace unreachable; skipping online IFEval test")
def test_ifeval_loader_returns_tasks():
    tasks = load_dataset("ifeval", limit=3)
    assert len(tasks) >= 1
    for t in tasks:
        assert t.dataset == "ifeval"
        assert isinstance(t.query, str) and t.query.strip()
        instructions = t.metadata.get("ifeval_instructions")
        assert isinstance(instructions, list) and len(instructions) >= 1
        first = instructions[0]
        assert "id" in first
        assert isinstance(first["id"], str) and first["id"]
        assert "kwargs" in first and isinstance(first["kwargs"], dict)
        assert t.json_schema is None
        assert t.required_keys is None
