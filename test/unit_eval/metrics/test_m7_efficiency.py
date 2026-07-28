from __future__ import annotations

from eval.metrics import m7_efficiency
from eval.metrics.types import TrialResult


def _t(turns: int, in_tok: int, out_tok: int) -> TrialResult:
    return TrialResult(
        trial_id="x",
        task_id="x",
        dataset="d",
        runner="harness",
        turns=turns,
        input_tokens=in_tok,
        output_tokens=out_tok,
    )


class TestEfficiency:
    def test_step_token_formulas(self):
        trials = [_t(2, 100, 100), _t(4, 300, 100)]
        # mean_turns = 3, mean_tokens = 300
        # step_eff = 0.5 / 3 = 0.16666...
        # token_eff = 0.5 / 0.3 = 1.6666...
        s = m7_efficiency.compute(trials, tsr=0.5)
        assert s.metric_id == "M7"
        assert abs(s.breakdown["mean_turns"] - 3.0) < 1e-9
        assert abs(s.breakdown["mean_tokens"] - 300.0) < 1e-9
        assert abs(s.breakdown["step_eff"] - (0.5 / 3.0)) < 1e-9
        assert abs(s.breakdown["token_eff"] - (0.5 / 0.3)) < 1e-9
        assert s.value == s.breakdown["token_eff"]

    def test_zero_division_safe(self):
        s = m7_efficiency.compute([_t(0, 0, 0)], tsr=1.0)
        assert s.breakdown["step_eff"] == 0.0
        assert s.breakdown["token_eff"] == 0.0
