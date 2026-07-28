"""
(en) Offline / import-guard tests for ``eval.datasets.tau_bench``.

(kr) ``eval.datasets.tau_bench`` 오프라인·import 가드 테스트.
"""
from __future__ import annotations

import pytest

from eval.datasets import load_dataset

pytestmark = pytest.mark.eval_datasets


def _tau_bench_installed() -> bool:
    try:
        import tau_bench  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _tau_bench_installed(), reason="tau-bench optional package not installed")
def test_tau_bench_retail_loader_returns_tasks():
    tasks = load_dataset("tau_bench.retail", limit=3)
    assert len(tasks) == 3
    for t in tasks:
        assert t.dataset == "tau_bench.retail"
        assert t.category == "retail"
        assert t.system_prompt and len(t.system_prompt) > 100
        assert t.tools
        assert t.expected_answer == 1
        assert t.metadata.get("tau_bench", {}).get("domain") == "retail"
        assert "tau_bench_tools_info" in t.metadata


@pytest.mark.skipif(not _tau_bench_installed(), reason="tau-bench optional package not installed")
def test_tau_bench_airline_loader_limit():
    tasks = load_dataset("tau_bench.airline", limit=2)
    assert len(tasks) == 2
    assert all(t.dataset == "tau_bench.airline" for t in tasks)


@pytest.mark.skipif(not _tau_bench_installed(), reason="tau-bench optional package not installed")
def test_tau_bench_combined_respects_limit():
    tasks = load_dataset("tau_bench", limit=5)
    assert len(tasks) == 5
    datasets = {t.dataset for t in tasks}
    assert datasets <= {"tau_bench.retail", "tau_bench.airline"}
