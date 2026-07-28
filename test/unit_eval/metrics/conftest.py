"""
(en) Shared fixtures for M1–M10 unit tests: tiny synthetic trials with known properties
so each metric's expected value is hand-computable.

(kr) M1–M10 단위 테스트 공통 fixture. 기대값을 손으로 계산할 수 있는 작은 합성 trial을 제공.
"""
from __future__ import annotations

import pytest

from eval.metrics.types import ToolCallRecord, TrialResult


@pytest.fixture()
def trial_ok_simple() -> TrialResult:
    return TrialResult(
        trial_id="t1",
        task_id="bfcl.simple.001",
        dataset="bfcl_v3.simple",
        runner="harness",
        final_content='{"city": "seoul"}',
        final_structured={"city": "seoul"},
        tool_calls=[
            ToolCallRecord(name="rag__retrieve", arguments={"q": "Seoul population"}),
        ],
        turns=2,
        input_tokens=120,
        output_tokens=80,
    )


@pytest.fixture()
def trial_wrong_args() -> TrialResult:
    return TrialResult(
        trial_id="t2",
        task_id="bfcl.simple.001",
        dataset="bfcl_v3.simple",
        runner="naive",
        final_content="cannot answer",
        tool_calls=[
            ToolCallRecord(name="rag__retrieve", arguments={"q": "Busan population"}),
        ],
        turns=3,
        input_tokens=130,
        output_tokens=70,
    )


@pytest.fixture()
def trial_redundant_calls() -> TrialResult:
    return TrialResult(
        trial_id="t3",
        task_id="bfcl.multi.002",
        dataset="bfcl_v3.multiple",
        runner="naive",
        final_content="ok",
        tool_calls=[
            ToolCallRecord(name="search", arguments={"q": "exaone"}),
            ToolCallRecord(name="search", arguments={"q": "exaone"}),
            ToolCallRecord(name="search", arguments={"q": "exaone"}),
            ToolCallRecord(name="fetch", arguments={"url": "https://x"}),
        ],
        turns=5,
        input_tokens=400,
        output_tokens=120,
    )


@pytest.fixture()
def trial_irrelevance_abstain() -> TrialResult:
    return TrialResult(
        trial_id="t4",
        task_id="bfcl.irr.003",
        dataset="bfcl_v3.irrelevance",
        runner="harness",
        final_content="I don't think any of the provided tools apply.",
        tool_calls=[],
        turns=1,
        input_tokens=90,
        output_tokens=20,
    )


@pytest.fixture()
def trial_irrelevance_hallucinate() -> TrialResult:
    return TrialResult(
        trial_id="t5",
        task_id="bfcl.irr.003",
        dataset="bfcl_v3.irrelevance",
        runner="naive",
        final_content="",
        tool_calls=[
            ToolCallRecord(name="weather", arguments={"city": "Tokyo"}),
        ],
        turns=1,
        input_tokens=90,
        output_tokens=30,
    )
