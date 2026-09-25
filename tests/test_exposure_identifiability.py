from __future__ import annotations

import pytest

from dynnav.exposure_identifiability import (
    no_exposure_identifiability_bound,
    no_exposure_observation_probability,
    no_exposure_total_variation_distance,
)


@pytest.mark.parametrize("p", [0.0, 0.1, 0.5, 0.9, 1.0])
def test_no_exposure_observation_law_is_independent_of_closure_probability(
    p: float,
) -> None:
    assert no_exposure_observation_probability(
        closure_probability=p,
        observations=10_000,
    ) == 1.0


def test_distinct_closure_probabilities_are_observationally_equivalent_without_exposure() -> None:
    assert no_exposure_total_variation_distance(
        0.05,
        0.95,
        observations=1_000_000,
    ) == 0.0


def test_no_exposure_minimax_error_is_half_parameter_interval_width() -> None:
    result = no_exposure_identifiability_bound(p_lower=0.1, p_upper=0.9)
    assert not result.identifiable
    assert not result.observation_law_depends_on_p
    assert result.midpoint_estimate == pytest.approx(0.5)
    assert result.minimax_absolute_error == pytest.approx(0.4)


def test_identifiability_bound_collapses_only_if_parameter_is_already_known() -> None:
    result = no_exposure_identifiability_bound(p_lower=0.3, p_upper=0.3)
    assert result.identifiable
    assert result.minimax_absolute_error == 0.0
