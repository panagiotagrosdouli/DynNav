"""Read-only, manifest-grounded publication evidence for Streamlit.

This module never runs experiments and never upgrades claims automatically.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "paper" / "dynnav_r" / "evidence_manifest.json"
CLAIMS = ROOT / "CLAIM_EVIDENCE_MATRIX.md"

def load_manifest(path: Path = MANIFEST) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Publication evidence manifest must be a JSON object")
    required = {"paper_title", "claim_scope", "reviewer_measurement_expansion",
                "gazebo_release_candidate_probe"}
    missing = required - data.keys()
    if missing:
        raise ValueError("Publication evidence manifest missing: " + ", ".join(sorted(missing)))
    return data

def load_claim_rows(path: Path = CLAIMS) -> list[dict[str, str]]:
    """Parse the repository's four-column claim table; do not infer any status."""
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) != 4 or parts[2] not in {"SUPPORTED", "UNSUPPORTED"}:
            continue
        result.append({"Claim": parts[0], "Evidence": parts[1],
                       "Status": parts[2], "Boundary": parts[3]})
    if not result:
        raise ValueError("No supported/unsupported claims found in evidence matrix")
    return result

def publication_summary(manifest: dict) -> dict:
    """Expose only explicitly named pinned measurements, not invented estimates."""
    packet = manifest["reviewer_measurement_expansion"]
    aggregate = packet["aggregate"]
    comparator = aggregate["history_vs_state_only_exact_scenario_risk_difference"]
    return {
        "source_workflow_run_id": packet["run_id"],
        "scenario_count": packet["scenario_count"],
        "paired_seeds_per_scenario": packet["paired_execution_seeds_per_scenario"],
        "baseline_return_infeasible_rate": aggregate["state_only_exact"]["return_infeasible_rate"],
        "history_return_infeasible_rate": aggregate["history_exact"]["return_infeasible_rate"],
        "scenario_mean_difference": comparator["mean"],
        "scenario_bootstrap_95": comparator["bootstrap_95"],
        "improved_scenarios": comparator["improved_scenarios"],
        "nonworse_scenarios": comparator["nonworse_scenarios"],
    }

def gazebo_probe_summary(manifest: dict) -> dict:
    probe = manifest["gazebo_release_candidate_probe"]
    return {
        "workflow_run_id": probe["run_id"],
        "valid_trials": probe["valid_trials"],
        "navigation_success": probe["navigation_success"],
        "operational_irreversible_failures": probe["operational_irreversible_failures"],
        "interpretation": probe["interpretation"],
    }
