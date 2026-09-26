from __future__ import annotations

import pytest

from dynnav.causal_trigger_discovery import (
    binary_confounding_observational_difference,
)
from dynnav.distributional_recoverability import (
    parallel_corridor_frechet_return_bounds,
)
from dynnav.online_hazard_learning import naive_unexposed_as_open_limit


@pytest.mark.parametrize(
    ("corridors", "probability", "expected"),
    (
        (2, 0.5, (0.5, 1.0)),
        (2, 0.8, (0.2, 0.4)),
        (3, 0.8, (0.2, 0.6)),
        (5, 0.8, (0.2, 1.0)),
    ),
)
def test_g1_frechet_parallel_corridor_bounds(
    corridors: int,
    probability: float,
    expected: tuple[float, float],
) -> None:
    assert parallel_corridor_frechet_return_bounds(
        corridors,
        probability,
    ) == pytest.approx(expected)


def test_g3_naive_nonexposure_logging_has_expected_limit() -> None:
    assert naive_unexposed_as_open_limit(0.5, 0.7) == pytest.approx(0.35)


def test_g4_binary_confounding_control_has_zero_causal_but_nonzero_observed_effect() -> None:
    observed = binary_confounding_observational_difference(
        confounder_probability=0.5,
        treatment_given_high=0.8,
        treatment_given_low=0.2,
        outcome_given_high=0.8,
        outcome_given_low=0.1,
    )
    assert observed == pytest.approx(0.42)
