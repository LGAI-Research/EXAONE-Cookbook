from __future__ import annotations

from eval.judges.bfcl_any_of import BFCLAnyOfJudge
from eval.metrics._canonical import normalize_bfcl_value
from eval.metrics.types import ToolCallRecord, TrialResult


def test_normalize_bfcl_value_strips_entity_prefix():
    assert normalize_bfcl_value("Company Acme Corp") == "acme corp"
    assert normalize_bfcl_value("product Widget-X") == "widget-x"
    assert normalize_bfcl_value("The Seoul") == "seoul"


def test_bfcl_judge_accepts_prefixed_entity_argument():
    judge = BFCLAnyOfJudge()
    trial = TrialResult(
        trial_id="t1",
        task_id="bfcl.simple.001",
        dataset="bfcl_v3.simple",
        runner="harness",
        tool_calls=[
            ToolCallRecord(
                name="get_company",
                arguments={"name": "Company Acme Corp"},
            )
        ],
    )
    gold = {
        "bfcl_ground_truth": [
            {"get_company": {"name": ["Acme Corp", "ACME CORP"]}},
        ]
    }
    assert judge(trial=trial, gold=gold) == 1.0


def test_bfcl_judge_rejects_wrong_entity_after_normalization():
    judge = BFCLAnyOfJudge()
    trial = TrialResult(
        trial_id="t2",
        task_id="bfcl.simple.002",
        dataset="bfcl_v3.simple",
        runner="naive",
        tool_calls=[
            ToolCallRecord(
                name="get_company",
                arguments={"name": "Company Other Inc"},
            )
        ],
    )
    gold = {
        "bfcl_ground_truth": [
            {"get_company": {"name": ["Acme Corp"]}},
        ]
    }
    assert judge(trial=trial, gold=gold) == 0.0
