"""
(en) Online smoke test for `eval.datasets.halubench`. Verifies ≥1 task is
returned with non-empty grounding context and a PASS/FAIL label.

(kr) `eval.datasets.halubench` 온라인 스모크 테스트이다.
>=1개 태스크가 반환되고 grounding context가 비어있지 않으며 PASS/FAIL 라벨이 있는지 검증한다.
"""
from __future__ import annotations

import pytest

from eval.datasets import load_dataset
from eval.datasets._net import is_online

pytestmark = pytest.mark.eval_datasets


@pytest.mark.skipif(not is_online(), reason="HuggingFace unreachable; skipping online HaluBench test")
def test_halubench_loader_returns_tasks():
    tasks = load_dataset("halubench", limit=3)
    assert len(tasks) >= 1
    for t in tasks:
        assert t.dataset == "halubench"
        assert isinstance(t.query, str) and t.query.strip()
        assert isinstance(t.grounding_context, str) and t.grounding_context.strip()
        assert isinstance(t.expected_answer, dict)
        assert "answer" in t.expected_answer
        assert t.expected_answer.get("label") in {"PASS", "FAIL"}
