"""Unit tests for eval.report display normalization."""
from __future__ import annotations

from eval.report import compute_deltas, display_value, enrich_metrics, markdown_table
from eval.report import ComparisonReport, RunnerSummary


def test_m8_display_value_is_one_minus_redundancy():
    raw = {"value": 0.22, "name": "Redundancy Rate"}
    assert display_value("M8", raw) == 0.78
    assert display_value("M1", {"value": 0.5}) == 0.5


def test_enrich_metrics_adds_call_uniqueness_breakdown():
    enriched = enrich_metrics({"M8": {"value": 0.2, "name": "Redundancy Rate"}})
    assert enriched["M8"]["display_value"] == 0.8
    assert enriched["M8"]["breakdown"]["call_uniqueness"] == 0.8
    assert enriched["M8"]["breakdown"]["redundancy_rate"] == 0.2


def test_compute_deltas_uses_display_value_for_m8():
    naive = RunnerSummary("naive", {"M8": {"value": 0.4}})
    harness = RunnerSummary("harness", {"M8": {"value": 0.0}})
    deltas = compute_deltas({"naive": naive, "harness": harness})
    assert deltas["M8"] == 0.4  # (1-0) - (1-0.4)


def test_markdown_table_shows_call_uniqueness():
    report = ComparisonReport(
        timestamp="2026-05-28T00:00:00Z",
        datasets=["bfcl_v3.simple"],
        limit=1,
        pass_k_trials=1,
        n_tasks=1,
        model="test",
        base_url_slug="api.example.com",
        runners=["naive", "harness"],
        summaries={
            "naive": RunnerSummary("naive", {"M8": {"value": 0.2, "name": "Redundancy Rate"}}),
            "harness": RunnerSummary("harness", {"M8": {"value": 0.0, "name": "Redundancy Rate"}}),
        },
        deltas={"M8": 0.2},
        trials={},
    )
    md = markdown_table(report)
    assert "Call Uniqueness" in md
    assert "0.8000" in md
    assert "higher is better" in md.lower()
