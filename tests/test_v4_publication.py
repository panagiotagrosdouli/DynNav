from __future__ import annotations

from dynnav.experiments.v4_publication import (
    calibration_table_tex,
    primary_table_tex,
)


def _analysis() -> dict[str, object]:
    interval = {
        "estimate": -0.1,
        "lower": -0.2,
        "upper": -0.01,
        "confidence": 0.95,
        "scenario_count": 2,
    }
    return {
        "comparisons": {
            "belief_vs_detector_as_truth": {
                "baseline": "detector_as_truth",
                "mission_failure_difference": interval,
                "operational_failure_difference": interval,
                "conditional_return_risk_difference": interval,
                "conditional_brier_difference": interval,
                "conditional_path_length_difference": {
                    **interval,
                    "estimate": 0.5,
                    "lower": 0.2,
                    "upper": 0.8,
                },
            }
        },
        "calibration_metrics": {
            "belief": {
                "count": 100,
                "brier_score": 0.12,
                "calibration_in_the_large": -0.02,
                "expected_calibration_error": 0.04,
            }
        },
        "calibration": {},
    }


def test_primary_table_is_generated_only_from_analysis_values() -> None:
    table = primary_table_tex(_analysis())

    assert r"detector\_as\_truth" in table
    assert "-0.1000 [-0.2000, -0.0100]" in table
    assert "0.5000 [0.2000, 0.8000]" in table


def test_calibration_table_contains_frozen_scalar_metrics() -> None:
    table = calibration_table_tex(_analysis())

    assert "belief" in table
    assert "0.1200" in table
    assert "-0.0200" in table
    assert "0.0400" in table
    assert "100" in table
