"""
(en) Online smoke test for `eval.datasets.bfcl_v3`. Verifies each of the four
sub-categories yields >=1 EvalTask with the expected shape. Skipped offline.

(kr) `eval.datasets.bfcl_v3` 온라인 스모크 테스트이다.
4개 서브카테고리 각각이 기대 형태의 EvalTask를 >=1개 반환하는지 확인하며 오프라인에서는 skip된다.
"""
from __future__ import annotations

import pytest

from eval.datasets import load_dataset
from eval.datasets._net import is_online

pytestmark = pytest.mark.eval_datasets


@pytest.mark.skipif(not is_online(), reason="HuggingFace unreachable; skipping online BFCL test")
@pytest.mark.parametrize("category", ["simple", "multiple", "parallel", "irrelevance"])
def test_bfcl_loader_returns_tasks(category: str):
    tasks = load_dataset(f"bfcl_v3.{category}", limit=3)
    assert len(tasks) >= 1, f"expected ≥1 task for bfcl_v3.{category}"

    for t in tasks:
        assert t.dataset == f"bfcl_v3.{category}"
        assert t.category == category
        assert isinstance(t.query, str) and t.query.strip()
        assert isinstance(t.tools, list) and len(t.tools) >= 1
        if category == "irrelevance":
            assert t.expected_no_tools is True
            assert t.expected_tool_calls is None
        else:
            assert t.expected_no_tools is False
            assert t.expected_tool_calls is not None
            assert len(t.expected_tool_calls) >= 1
            call = t.expected_tool_calls[0]
            assert isinstance(call.name, str) and call.name
            assert isinstance(call.arguments, dict)


@pytest.mark.skipif(not is_online(), reason="HuggingFace unreachable; skipping online BFCL test")
def test_bfcl_top_level_aggregate_respects_limit():
    tasks = load_dataset("bfcl_v3", limit=4)
    assert len(tasks) == 4
    datasets_seen = {t.dataset for t in tasks}
    assert all(d.startswith("bfcl_v3.") for d in datasets_seen)
