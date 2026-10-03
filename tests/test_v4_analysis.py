from __future__ import annotations

import pytest

from dynnav.experiments.v4_analysis import (
    V4AnalysisRow,
    fixed_bin_calibration,
    paired_v4_comparison,
)


def _row(
    scenario: str,
    seed: int,
    planner: str,
    *,
    feasible: bool,
    prediction: float,
    path: float,
    family: str = "F1",
) -> V4AnalysisRow:
    return V4AnalysisRow(
        scenario=scenario,
        topology_family=family,
        seed=seed,
        planner=planner,
        observation_regime="O2",
        path_length=path,
        predicted_return_probability=prediction,
        return_feasible=feasible,
        mission_success=True,
        protocol_valid=True,
    )


def test_primary_comparison_is_scenario_weighted_and_paired() -> None:
    rows = [
        _row("a", 0, "detector", feasible=False, prediction=0.9, path=2),
        _row("a", 0, "belief", feasible=True, prediction=0.8, path=3),
        _row("a", 1, "detector", feasible=False, prediction=0.9, path=2),
        _row("a", 1, "belief", feasible=True, prediction=0.8, path=3),
        _row("b", 0, "detector", feasible=True, prediction=0.9, path=2),
        _row("b", 0, "belief", feasible=False, prediction=0.6, path=2),
    ]

    result = paired_v4_comparison(
        rows,
        proposed="belief",
        baseline="detector",
        observation_regime="O2",
        resamples=500,
        seed=4,
    )

    # Scenario a mean risk difference is -1; scenario b is +1.
    # Equal scenario weighting therefore gives zero.
    assert result["risk_difference"]["estimate"] == pytest.approx(0.0)
    assert result["scenario_count"] == 2
    assert result["paired_seed_count"] == 3


def test_incomplete_pairing_is_rejected() -> None:
    rows = [
        _row("a", 0, "belief", feasible=True, prediction=0.8, path=3),
    ]
    with pytest.raises(ValueError, match="incomplete planner pairing"):
        paired_v4_comparison(
            rows,
            proposed="belief",
            baseline="detector",
            observation_regime="O2",
            resamples=500,
        )


def test_fixed_calibration_bins_include_probability_one() -> None:
    rows = [
        _row("a", 0, "belief", feasible=True, prediction=1.0, path=2),
        _row("a", 1, "belief", feasible=False, prediction=0.95, path=2),
    ]

    bins = fixed_bin_calibration(
        rows,
        planner="belief",
        observation_regime="O2",
    )

    assert bins[-1].count == 2
    assert bins[-1].mean_prediction == pytest.approx(0.975)
    assert bins[-1].empirical_frequency == pytest.approx(0.5)
