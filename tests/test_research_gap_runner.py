from __future__ import annotations

from dynnav.experiments.research_gap_program import run_research_gap_program


def test_research_gap_program_smoke() -> None:
    result = run_research_gap_program(trials=100, seed=7)

    assert len(result["G1_dependence_ambiguity"]) == 13
    assert len(result["G1_dependence_shift_execution"]) == 6
    assert len(result["G2_activation_belief_frontier"]) == 48
    assert len(result["G3_logging_bias_control"]) == 4
    assert len(result["G3_online_policy_benchmark"]) == 4
    assert len(result["G4_interventional_trigger_effect"]) == 3
    assert result["G4_causal_graph_recovery"]["injected_positive_edges"] == 3
    assert len(result["G5_history_compression_counts"]) == 4
    assert len(result["G5_search_scaling"]) == 5

    g1 = result["G1_dependence_ambiguity"]
    two_corridor_half = [
        row
        for row in g1
        if row["corridors"] == 2
        and row["marginal_probability"] == 0.5
        and row["ambiguity_width"] > 0.0
    ][0]
    assert two_corridor_half["worst_case_return"] == 0.5
    assert two_corridor_half["independent_return"] == 0.75

    g5 = result["G5_history_compression_counts"][-1]
    assert g5["raw_hazard_count"] == 12
    assert g5["closure_event_count"] == 2
    assert g5["quotient_subset_state_count"] == 4
