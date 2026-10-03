from __future__ import annotations

import pytest

from dynnav.experiments.v4_correlation_benchmark import (
    run_correlation_reliability_benchmark,
)


def _lookup(records, topology: str, p: float, rho: float):
    return next(
        row
        for row in records
        if row.topology == topology
        and row.marginal_probability == p
        and row.correlation == rho
    )


def test_independence_limit_matches_joint_model_at_zero_correlation() -> None:
    records = run_correlation_reliability_benchmark(
        marginal_probabilities=(0.5,),
        correlations=(0.0,),
    )

    for row in records:
        assert row.joint_return_probability == pytest.approx(
            row.independent_return_probability
        )
        assert row.signed_independence_error == pytest.approx(0.0)


def test_same_positive_correlation_can_reverse_error_direction_by_topology() -> None:
    records = run_correlation_reliability_benchmark(
        marginal_probabilities=(0.5,),
        correlations=(1.0,),
    )

    parallel = _lookup(records, "parallel_joint_cut", 0.5, 1.0)
    serial = _lookup(records, "serial_any_cut", 0.5, 1.0)

    assert parallel.independent_return_probability == pytest.approx(0.75)
    assert parallel.joint_return_probability == pytest.approx(0.50)
    assert parallel.signed_independence_error == pytest.approx(0.25)

    assert serial.independent_return_probability == pytest.approx(0.25)
    assert serial.joint_return_probability == pytest.approx(0.50)
    assert serial.signed_independence_error == pytest.approx(-0.25)


def test_common_cause_formulas_match_analytic_reliability() -> None:
    p = 0.8
    rho = 0.75
    records = run_correlation_reliability_benchmark(
        marginal_probabilities=(p,),
        correlations=(rho,),
    )

    parallel = _lookup(records, "parallel_joint_cut", p, rho)
    serial = _lookup(records, "serial_any_cut", p, rho)

    expected_parallel = 1.0 - (rho * p + (1.0 - rho) * p**2)
    expected_serial = (
        rho * (1.0 - p)
        + (1.0 - rho) * (1.0 - p) ** 2
    )

    assert parallel.joint_return_probability == pytest.approx(
        expected_parallel
    )
    assert serial.joint_return_probability == pytest.approx(expected_serial)
