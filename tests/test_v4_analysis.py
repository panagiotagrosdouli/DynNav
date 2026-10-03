from __future__ import annotations

import pytest

from dynnav.experiments.v4_analysis import (
    V4AnalysisRow,
    calibration_metrics,
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
    mission_success: bool = True,
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
        mission_success=mission_success,
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

    # Scenario a conditional return-risk difference is -1; scenario b is +1.
    # Equal scenario weighting therefore gives zero.
    assert result["conditional_return_risk_difference"]["estimate"] == pytest.approx(0.0)
    assert result["operational_failure_difference"]["estimate"] == pytest.approx(0.0)
    assert result["mission_failure_difference"]["estimate"] == pytest.approx(0.0)
    assert result["scenario_count"] == 2
    assert result["paired_seed_count"] == 3
    assert result["joint_mission_success_pair_count"] == 3


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


def test_asymmetric_mission_failure_is_not_silently_dropped() -> None:
    rows = [
        _row(
            "a",
            0,
            "detector",
            feasible=True,
            prediction=0.9,
            path=2,
            mission_success=True,
        ),
        _row(
            "a",
            0,
            "belief",
            feasible=False,
            prediction=float("nan"),
            path=0,
            mission_success=False,
        ),
    ]

    result = paired_v4_comparison(
        rows,
        proposed="belief",
        baseline="detector",
        observation_regime="O2",
        resamples=500,
        seed=4,
    )

    assert result["paired_seed_count"] == 1
    assert result["joint_mission_success_pair_count"] == 0
    assert result["asymmetric_mission_success_pair_count"] == 1
    assert result["mission_failure_difference"]["estimate"] == pytest.approx(1.0)
    assert result["operational_failure_difference"]["estimate"] == pytest.approx(1.0)
    assert result["conditional_return_risk_difference"] is None
    assert result["conditional_brier_difference"] is None
    assert result["conditional_path_length_difference"] is None


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


def test_calibration_metrics_known_answer() -> None:
    rows = [
        _row("a", 0, "belief", feasible=True, prediction=0.8, path=2),
        _row("a", 1, "belief", feasible=False, prediction=0.2, path=2),
    ]

    metrics = calibration_metrics(
        rows,
        planner="belief",
        observation_regime="O2",
    )

    assert metrics["count"] == 2
    assert metrics["brier_score"] == pytest.approx(0.04)
    assert metrics["mean_prediction"] == pytest.approx(0.5)
    assert metrics["empirical_frequency"] == pytest.approx(0.5)
    assert metrics["calibration_in_the_large"] == pytest.approx(0.0)
    assert metrics["expected_calibration_error"] == pytest.approx(0.2)
