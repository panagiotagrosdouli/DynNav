from __future__ import annotations

import pytest

from dynnav.experiments.joint_cut_counterexample import (
    joint_cut_world,
    run_joint_cut_counterexample,
    summarize_joint_cut_counterexample,
)


def test_joint_cut_direct_path_has_parallel_return_failure_probability() -> None:
    grid, start, goal, safe, model = joint_cut_world(0.8)
    assert grid.passable(start)
    assert grid.passable(goal)
    assert safe == {start}
    assert len(model.closures) == 2
    assert model.closures[0].closure_cell != model.closures[1].closure_cell


def test_exact_history_distinguishes_equal_length_joint_cut_routes() -> None:
    records = run_joint_cut_counterexample(
        closure_probabilities=(0.8,),
        recoverability_weights=(8.0,),
    )
    exact = next(row for row in records if row.planner == "history_exact")
    cut = next(row for row in records if row.planner == "history_cut")

    # Both selected routes have equal geometric length.  The scientific signal
    # is therefore entirely in activated history and return-connectivity risk.
    assert exact.path_length == cut.path_length == 6

    assert exact.activated_closure_count == 0
    assert exact.final_exact_return_probability == pytest.approx(1.0)

    assert cut.activated_closure_count == 2
    assert cut.final_exact_return_probability == pytest.approx(1.0 - 0.8**2)
    assert cut.final_cut_return_estimate == pytest.approx(1.0)


def test_summary_reports_approximation_boundary() -> None:
    summary = summarize_joint_cut_counterexample(run_joint_cut_counterexample())
    assert summary["cut_optimism_cases"] > 0
    assert summary["route_disagreement_rate"] > 0.0
