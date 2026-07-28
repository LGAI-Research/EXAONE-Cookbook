from __future__ import annotations

from eval.metrics import m3_tool_selection
from eval.metrics.m3_tool_selection import jaccard, normalize_tool_name, strict_match
from eval.metrics.types import ToolCallRecord


class TestNormalizeName:
    def test_strips_catalog_prefix(self):
        assert normalize_tool_name("rag__retrieve") == "retrieve"
        assert normalize_tool_name("rag.retrieve") == "retrieve"
        assert normalize_tool_name("retrieve") == "retrieve"

    def test_lower_case(self):
        assert normalize_tool_name("RAG__Retrieve") == "retrieve"


class TestStrict:
    def test_multiset_equality(self):
        assert strict_match(["a", "b"], ["b", "a"])
        assert not strict_match(["a", "a"], ["a"])

    def test_empty_both(self):
        assert strict_match([], [])


class TestJaccard:
    def test_perfect_overlap(self):
        assert jaccard(["a", "b"], ["a", "b"]) == 1.0

    def test_partial(self):
        assert jaccard(["a", "b"], ["a", "c"]) == 1 / 3

    def test_empty_empty_is_one(self):
        assert jaccard([], []) == 1.0


class TestCompute:
    def test_harness_prefix_matches_logical_gold(self, trial_ok_simple):
        gold = {trial_ok_simple.task_id: [ToolCallRecord(name="rag.retrieve", arguments={"q": "x"})]}
        s = m3_tool_selection.compute([trial_ok_simple], gold)
        assert s.value == 1.0
        assert s.breakdown["jaccard"] == 1.0

    def test_mismatched_tool_zero_strict_but_nonzero_jaccard(self, trial_ok_simple):
        gold = {
            trial_ok_simple.task_id: [
                ToolCallRecord(name="rag.retrieve", arguments={"q": "x"}),
                ToolCallRecord(name="extra_tool", arguments={}),
            ]
        }
        s = m3_tool_selection.compute([trial_ok_simple], gold)
        assert s.value == 0.0  # multiset mismatch
        assert 0 < s.breakdown["jaccard"] < 1
