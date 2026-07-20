"""Tests for the controlled counterexample validation gate."""

from validate_counterexample import ValidationThresholds, relative_gap, validate_seed


def test_relative_gap_is_symmetric() -> None:
    assert relative_gap(2.0, 1.0) == relative_gap(1.0, 2.0)


def test_default_counterexample_validates() -> None:
    assert validate_seed(0, ValidationThresholds()) == []


def test_overly_strict_recoverability_threshold_fails() -> None:
    errors = validate_seed(
        0,
        ValidationThresholds(min_recoverability_gap=1.0),
    )
    assert any("recoverability gap" in error for error in errors)
