from __future__ import annotations

import pytest

from eval.metrics import m6_schema_adherence
from eval.metrics.m6_schema_adherence import SchemaSpec
from eval.metrics.types import TrialResult


def _try_load() -> bool:
    try:
        m6_schema_adherence._load_extractors()
        return True
    except Exception:
        return False


_HAS_EXAONE_OUTPUT = _try_load()


@pytest.mark.skipif(not _HAS_EXAONE_OUTPUT, reason="exaone.output not importable")
class TestStrictVsLoose:
    def test_strict_pass_when_valid_json(self):
        t = TrialResult(
            trial_id="x",
            task_id="t1",
            dataset="d",
            runner="harness",
            final_content='{"answer": "ok"}',
        )
        spec = SchemaSpec(required_keys=["answer"])
        strict, loose = m6_schema_adherence.score_trial(t, spec)
        assert strict and loose

    def test_loose_recovers_from_trailing_text(self):
        t = TrialResult(
            trial_id="x",
            task_id="t1",
            dataset="d",
            runner="harness",
            final_content='Sure!\n```json\n{"answer": "ok"}\n```\nthanks',
        )
        spec = SchemaSpec(required_keys=["answer"])
        _, loose = m6_schema_adherence.score_trial(t, spec)
        assert loose, "AutoRepair should recover the fenced JSON"

    def test_repair_gain_is_visible_in_summary(self):
        clean = TrialResult(
            trial_id="a",
            task_id="t1",
            dataset="d",
            runner="harness",
            final_content='{"answer": "ok"}',
        )
        dirty = TrialResult(
            trial_id="b",
            task_id="t2",
            dataset="d",
            runner="harness",
            final_content='Sure! ```json\n{"answer": "ok"}\n```',
        )
        spec = SchemaSpec(required_keys=["answer"])
        s = m6_schema_adherence.compute(
            [clean, dirty],
            {"t1": spec, "t2": spec},
        )
        assert s.metric_id == "M6"
        assert s.breakdown["loose"] >= s.breakdown["strict"]
        assert s.breakdown["repair_gain"] >= 0.0
