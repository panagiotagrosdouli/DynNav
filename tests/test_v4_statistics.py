from __future__ import annotations

import pytest

from dynnav.experiments.v4_statistics import (
    brier_score,
    calibration_summary,
    fixed_bin_ece,
    hierarchical_bootstrap,
    scenario_paired_differences,
)


def test_brier_known_answer() -> None:
    assert brier_score([0.0, 1.0, 0.5, 0.5], [0, 1, 1, 0]) == pytest.approx(0.125)


def test_calibration_summary_is_zero_for_perfect_predictions() -> None:
    summary = calibration_summary([0.0, 1.0, 0.0, 1.0], [0, 1, 0, 1])
    assert summary.brier_score == pytest.approx(0.0)
    assert summary.calibration_in_the_large == pytest.approx(0.0)
    assert summary.expected_calibration_error == pytest.approx(0.0)


def test_fixed_bin_ece_detects_overconfidence() -> None:
    assert fixed_bin_ece([0.9, 0.9, 0.9, 0.9], [1, 0, 0, 0]) == pytest.approx(0.65)


def test_scenario_paired_differences_require_exact_pairing() -> None:
    rows = [
        {"scenario_id": "a", "execution_seed": 0, "planner": "base", "risk": 1},
        {"scenario_id": "a", "execution_seed": 0, "planner": "new", "risk": 0},
        {"scenario_id": "a", "execution_seed": 1, "planner": "base", "risk": 0},
        {"scenario_id": "a", "execution_seed": 1, "planner": "new", "risk": 0},
        {"scenario_id": "b", "execution_seed": 0, "planner": "base", "risk": 1},
        {"scenario_id": "b", "execution_seed": 0, "planner": "new", "risk": 1},
    ]
    paired = scenario_paired_differences(
        rows,
        baseline="base",
        proposed="new",
        value_field="risk",
    )
    assert paired == {"a": [-1.0, 0.0], "b": [0.0]}


def test_hierarchical_bootstrap_estimate_equal_weights_scenarios() -> None:
    interval = hierarchical_bootstrap(
        {
            "large": [1.0] * 100,
            "small": [-1.0],
        },
        resamples=500,
        seed=3,
    )
    assert interval.estimate == pytest.approx(0.0)
    assert interval.scenario_count == 2


def test_unpaired_trial_is_rejected() -> None:
    rows = [
        {"scenario_id": "a", "execution_seed": 0, "planner": "base", "risk": 1},
    ]
    with pytest.raises(ValueError, match="unpaired"):
        scenario_paired_differences(
            rows,
            baseline="base",
            proposed="new",
            value_field="risk",
        )
