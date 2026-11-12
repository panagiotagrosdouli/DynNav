"""Regression checks for manifest-derived dashboard claims.

No Streamlit runtime is needed to verify the source-to-display contract.
"""
from __future__ import annotations

import json

import pytest

from dynnav_dashboard.publication_evidence import (
    gazebo_probe_summary, load_claim_rows, load_manifest, publication_summary,
)


def test_pinned_publication_summary_matches_actual_manifest():
    data = load_manifest()
    source = data["reviewer_measurement_expansion"]
    result = publication_summary(data)
    assert result["source_workflow_run_id"] == source["run_id"]
    assert result["scenario_count"] == source["scenario_count"]
    assert result["paired_seeds_per_scenario"] == source["paired_execution_seeds_per_scenario"]
    assert result["baseline_return_infeasible_rate"] == source["aggregate"]["state_only_exact"]["return_infeasible_rate"]
    assert result["history_return_infeasible_rate"] == source["aggregate"]["history_exact"]["return_infeasible_rate"]
    assert result["scenario_bootstrap_95"] == source["aggregate"]["history_vs_state_only_exact_scenario_risk_difference"]["bootstrap_95"]


def test_gazebo_probe_is_not_misrepresented_as_comparative_efficacy():
    data = load_manifest()
    result = gazebo_probe_summary(data)
    assert result["valid_trials"] == data["gazebo_release_candidate_probe"]["valid_trials"]
    assert "no stable comparative" in result["interpretation"].lower()


def test_claim_rows_include_negative_results_and_boundaries():
    rows = load_claim_rows()
    assert any(row["Status"] == "SUPPORTED" for row in rows)
    assert any(row["Status"] == "UNSUPPORTED" for row in rows)
    assert all(row["Claim"] and row["Boundary"] for row in rows)


def test_manifest_validation_rejects_missing_source(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps({"paper_title": "example"}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing"):
        load_manifest(p)


def test_claim_matrix_validation_rejects_empty_source(tmp_path):
    p = tmp_path / "claims.md"
    p.write_text("# No evidence yet\n", encoding="utf-8")
    with pytest.raises(ValueError, match="No supported"):
        load_claim_rows(p)
