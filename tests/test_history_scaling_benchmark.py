from __future__ import annotations

import json

import pytest

from dynnav.experiments.history_scaling_benchmark import (
    forced_history_corridor,
    run_history_scaling_benchmark,
    summarize_history_scaling,
    write_history_scaling_artifacts,
)


def test_forced_corridor_accumulates_requested_number_of_triggers() -> None:
    grid, start, goal, model = forced_history_corridor(4)

    assert grid.width == 7
    assert start == (0, 0)
    assert goal == (6, 0)
    assert len(model.closures) == 4


def test_exact_and_path_reliability_agree_on_single_corridor() -> None:
    records = run_history_scaling_benchmark(
        hazard_counts=(1, 2, 4),
        closure_probability=0.1,
    )
    by_key = {(row.hazard_count, row.planner): row for row in records}

    for count in (1, 2, 4):
        exact = by_key[(count, "exact")]
        approximate = by_key[(count, "approx_redundant")]
        expected = 0.9**count
        assert exact.success and approximate.success
        assert exact.final_return_probability == pytest.approx(expected)
        assert approximate.final_return_probability == pytest.approx(expected)
        assert approximate.final_return_probability == pytest.approx(
            exact.final_return_probability
        )


def test_scaling_summary_reports_runtime_without_asserting_speedup() -> None:
    records = run_history_scaling_benchmark(hazard_counts=(1, 2))
    summary = summarize_history_scaling(records)

    assert summary["hazard_counts"] == [1, 2]
    assert summary["exact_max_planning_time_ms"] >= 0.0
    assert summary["approx_max_planning_time_ms"] >= 0.0
    assert summary["max_probability_absolute_error"] == pytest.approx(0.0)
    assert "planning_time_ratio_exact_over_approx" in summary["per_count"]["2"]


def test_scaling_benchmark_writes_raw_artifacts(tmp_path) -> None:
    records = run_history_scaling_benchmark(hazard_counts=(1, 2))
    write_history_scaling_artifacts(records, tmp_path)

    assert (tmp_path / "trials.csv").exists()
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload["hazard_counts"] == [1, 2]
