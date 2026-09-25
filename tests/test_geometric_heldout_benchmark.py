from __future__ import annotations

from dynnav.experiments.geometric_heldout_benchmark import (
    frozen_geometric_scenarios,
    run_geometric_heldout_benchmark,
    summarize_geometric_heldout,
)


def test_geometric_scenarios_are_distinct_and_valid() -> None:
    scenarios = frozen_geometric_scenarios()
    assert {scenario.name for scenario in scenarios} == {
        "fork",
        "l_room",
        "chamber_two_trigger",
    }
    assert len({(scenario.grid.width, scenario.grid.height) for scenario in scenarios}) == 3
    for scenario in scenarios:
        scenario.grid.validate()
        scenario.model.validate(scenario.grid)
        assert scenario.start in scenario.safe
        assert scenario.grid.passable(scenario.start)
        assert scenario.grid.passable(scenario.goal)


def test_history_conditioning_reduces_trigger_activation_on_frozen_geometries() -> None:
    records = run_geometric_heldout_benchmark(seeds=tuple(range(20)))
    summary = summarize_geometric_heldout(records)
    for scenario, block in summary.items():
        shortest = block["shortest"]
        state_only = block["state_only_single"]
        state_only_exact = block["state_only_exact"]
        history = block["history_exact"]

        assert shortest["activated_closure_count"] > 0, scenario
        assert state_only["activated_closure_count"] == shortest["activated_closure_count"], scenario
        assert state_only["path_length"] == shortest["path_length"], scenario
        assert state_only_exact["activated_closure_count"] == shortest[
            "activated_closure_count"
        ], scenario
        assert state_only_exact["path_length"] == shortest["path_length"], scenario
        assert history["activated_closure_count"] < shortest["activated_closure_count"], scenario
        assert history["irreversible_failure_rate"] <= shortest["irreversible_failure_rate"], scenario


def test_state_only_outcomes_remain_paired_with_shortest() -> None:
    records = run_geometric_heldout_benchmark(seeds=tuple(range(30)))
    summary = summarize_geometric_heldout(records)
    for block in summary.values():
        effect = block["paired_binary_effects_vs_shortest"]["state_only_single"]
        exact_effect = block["paired_binary_effects_vs_shortest"]["state_only_exact"]
        assert effect["risk_difference"] == 0.0
        assert effect["discordant_pairs"] == 0
        assert exact_effect["risk_difference"] == 0.0
        assert exact_effect["discordant_pairs"] == 0
