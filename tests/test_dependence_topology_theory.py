from __future__ import annotations

import pytest

from dynnav.dependence_topology_theory import (
    TwoHazardDependencePoint,
    dependence_effect_relative_to_independence,
    parallel_return_probability,
    serial_return_probability,
)


def test_common_cause_has_opposite_effect_in_parallel_and_serial_topologies() -> None:
    point = TwoHazardDependencePoint(
        p_first=0.5,
        p_second=0.5,
        joint_closure=0.5,
    )
    assert parallel_return_probability(point) == pytest.approx(0.5)
    assert serial_return_probability(point) == pytest.approx(0.5)
    parallel_delta, serial_delta = dependence_effect_relative_to_independence(point)
    assert parallel_delta == pytest.approx(-0.25)
    assert serial_delta == pytest.approx(0.25)


def test_anti_correlation_reverses_the_signs() -> None:
    point = TwoHazardDependencePoint(
        p_first=0.5,
        p_second=0.5,
        joint_closure=0.0,
    )
    assert parallel_return_probability(point) == pytest.approx(1.0)
    assert serial_return_probability(point) == pytest.approx(0.0)
    parallel_delta, serial_delta = dependence_effect_relative_to_independence(point)
    assert parallel_delta == pytest.approx(0.25)
    assert serial_delta == pytest.approx(-0.25)


def test_invalid_joint_probability_rejected_by_frechet_bounds() -> None:
    point = TwoHazardDependencePoint(
        p_first=0.2,
        p_second=0.3,
        joint_closure=0.25,
    )
    with pytest.raises(ValueError, match="Frechet"):
        point.validate()
