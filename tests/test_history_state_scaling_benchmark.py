from __future__ import annotations

from dynnav.experiments.history_state_scaling_benchmark import (
    run_history_state_scaling_benchmark,
    summarize_history_state_scaling,
)


def test_scaling_benchmark_records_all_planners_per_module() -> None:
    records = run_history_state_scaling_benchmark(module_counts=(1, 2, 3))
    assert len(records) == 9
    assert {row.planner for row in records} == {
        "shortest_augmented",
        "history_exact",
        "history_cut",
    }
    assert all(row.success for row in records)


def test_exact_and_cut_preserve_same_route_in_series_family() -> None:
    records = run_history_state_scaling_benchmark(
        module_counts=(1, 2, 3, 4),
        closure_probability=0.8,
        recoverability_weight=8.0,
    )
    for modules in (1, 2, 3, 4):
        exact = next(
            row for row in records
            if row.module_count == modules and row.planner == "history_exact"
        )
        cut = next(
            row for row in records
            if row.module_count == modules and row.planner == "history_cut"
        )
        assert exact.geometric_length == cut.geometric_length
        assert exact.activated_closure_count == cut.activated_closure_count


def test_summary_exposes_nodes_and_latency_by_module() -> None:
    summary = summarize_history_state_scaling(
        run_history_state_scaling_benchmark(module_counts=(1, 2))
    )
    for planner in ("shortest_augmented", "history_exact", "history_cut"):
        assert summary[planner]["max_modules"] == 2
        assert set(summary[planner]["per_module"]) == {"1", "2"}
        assert summary[planner]["max_nodes_expanded"] > 0
