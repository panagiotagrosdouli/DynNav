from __future__ import annotations

import pytest

from dynnav.experiments.cut_scaling_benchmark import (
    run_cut_scaling_benchmark,
    summarize_cut_scaling,
)


def test_series_cut_approximation_matches_exact_for_all_scales() -> None:
    records = run_cut_scaling_benchmark(
        hazard_counts=(1, 2, 4, 6),
        closure_probability=0.2,
    )
    cut = [row for row in records if row.method == "critical_cut"]
    assert cut
    assert all(row.absolute_error == pytest.approx(0.0) for row in cut)


def test_series_probability_matches_independent_survival_product() -> None:
    records = run_cut_scaling_benchmark(
        hazard_counts=(3,),
        closure_probability=0.25,
    )
    exact = next(row for row in records if row.method == "exact")
    assert exact.probability == pytest.approx(0.75 ** 3)


def test_summary_contains_all_hazard_counts_and_zero_max_error() -> None:
    summary = summarize_cut_scaling(
        run_cut_scaling_benchmark(hazard_counts=(1, 2, 4), closure_probability=0.1)
    )
    assert summary["hazard_counts"] == [1, 2, 4]
    assert summary["max_cut_absolute_error"] == pytest.approx(0.0)
