from __future__ import annotations

from eval.metrics import m8_redundancy


class TestRedundancy:
    def test_no_duplicates(self, trial_ok_simple):
        s = m8_redundancy.compute([trial_ok_simple])
        assert s.value == 0.0
        assert s.breakdown["duplicate_calls_total"] == 0.0
        assert s.breakdown["total_calls"] == 1.0

    def test_hard_loop(self, trial_redundant_calls):
        # 4 calls: search × 3 (2 duplicates) + fetch × 1 → dup = 2, total = 4
        s = m8_redundancy.compute([trial_redundant_calls])
        assert s.breakdown["duplicate_calls_total"] == 2.0
        assert s.breakdown["total_calls"] == 4.0
        assert s.value == 0.5

    def test_micro_vs_macro_differ(self, trial_ok_simple, trial_redundant_calls):
        s = m8_redundancy.compute([trial_ok_simple, trial_redundant_calls])
        # micro = 2 / 5 = 0.4
        assert abs(s.breakdown["micro"] - 0.4) < 1e-9
        # macro = (0 + 0.5) / 2 = 0.25
        assert abs(s.breakdown["macro"] - 0.25) < 1e-9

    def test_canonical_args_normalized_match_ledger_rule(self):
        from eval.metrics.types import ToolCallRecord, TrialResult

        # args order differs but should be treated as duplicate (sort_keys)
        t = TrialResult(
            trial_id="x", task_id="x", dataset="d", runner="naive",
            tool_calls=[
                ToolCallRecord(name="f", arguments={"a": 1, "b": 2}),
                ToolCallRecord(name="f", arguments={"b": 2, "a": 1}),
            ],
        )
        s = m8_redundancy.compute([t])
        assert s.value == 0.5
