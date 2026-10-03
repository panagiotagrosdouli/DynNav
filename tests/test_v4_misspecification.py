from __future__ import annotations

from dynnav.experiments.v4_misspecification import (
    load_misspecification_matrix,
)


def test_frozen_misspecification_matrix_contains_predeclared_conditions() -> None:
    matrix = load_misspecification_matrix()

    assert matrix.true_regime == "O2"
    assert matrix.true_sensitivity == 0.85
    assert matrix.true_specificity == 0.85

    by_id = {condition.condition_id: condition for condition in matrix.conditions}
    assert set(by_id) == {
        "M0_correct",
        "M1_sensor_overconfident",
        "M2_sensor_weak",
        "M3_miss_rate_error",
        "M4_false_alarm_error",
        "Q_minus_0p2",
        "Q_plus_0p2",
    }
    assert by_id["M0_correct"].assumed_sensitivity == 0.85
    assert by_id["M0_correct"].assumed_specificity == 0.85
    assert by_id["Q_minus_0p2"].assumed_arming_offset == -0.20
    assert by_id["Q_plus_0p2"].assumed_arming_offset == 0.20
