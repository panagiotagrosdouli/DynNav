from __future__ import annotations

from dynnav.experiments.geometric_pareto_benchmark import (
    HARD_THRESHOLDS,
    SOFT_WEIGHTS,
    run_geometric_pareto_benchmark,
    summarize_geometric_pareto,
)


def test_parameter_grid_matches_frozen_protocol() -> None:
    assert SOFT_WEIGHTS == (0.0, 1.0, 2.0, 4.0, 8.0, 16.0)
    assert HARD_THRESHOLDS == (0.50, 0.70, 0.80, 0.90, 0.95, 0.99)


def test_pareto_sweep_preserves_planning_failure_semantics() -> None:
    records = run_geometric_pareto_benchmark(seeds=(0, 1, 2))
    for row in records:
        if row.planner_success:
            assert row.path_length is not None
            assert row.activated_closure_count is not None
            assert row.irreversible_failure is not None
        else:
            assert row.path_length is None
            assert row.activated_closure_count is None
            assert row.irreversible_failure is None


def test_summary_retains_complete_predeclared_grid() -> None:
    records = run_geometric_pareto_benchmark(seeds=(0, 1))
    summary = summarize_geometric_pareto(records)
    assert set(summary) == {"fork", "l_room", "chamber_two_trigger"}
    expected = len(SOFT_WEIGHTS) + len(HARD_THRESHOLDS)
    for entries in summary.values():
        assert len(entries) == expected
        soft = [row for row in entries if row["family"] == "soft_history"]
        hard = [row for row in entries if row["family"] == "hard_return"]
        assert [row["parameter"] for row in soft] == list(SOFT_WEIGHTS)
        assert [row["parameter"] for row in hard] == list(HARD_THRESHOLDS)
