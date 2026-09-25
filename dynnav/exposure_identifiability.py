"""Identifiability limits for exposure-gated topology-hazard learning.

The cold-start lockout result says a strict gate can keep the posterior fixed.
This module states the stronger statistical fact behind that behavior.

If trigger-conditioned closure outcomes are observed only after exposure, and a
policy never exposes the trigger and receives no informative side channel, then
the complete observation law is identical for every closure probability p.
Therefore p is not identifiable from those data.

For a parameter known only to lie in [p_lower, p_upper], every estimator based
on such no-exposure data has worst-case absolute error at least half the
interval width. A constant midpoint estimator attains that bound, so it is the
exact minimax error under the stated information structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class NoExposureIdentifiabilityResult:
    p_lower: float
    p_upper: float
    observation_law_depends_on_p: bool
    identifiable: bool
    minimax_absolute_error: float
    midpoint_estimate: float


def no_exposure_observation_probability(
    *,
    closure_probability: float,
    observations: int = 1,
) -> float:
    """Probability of the unique no-exposure observation sequence.

    With no exposure and no side information, each opportunity yields the same
    null observation regardless of the latent closure probability. Hence the
    unique length-n observation sequence has probability one for every p.
    """

    if not isfinite(closure_probability) or not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be finite and in [0, 1]")
    if observations < 0:
        raise ValueError("observations must be non-negative")
    return 1.0


def no_exposure_total_variation_distance(
    p_first: float,
    p_second: float,
    *,
    observations: int = 1,
) -> float:
    """Total-variation distance between two no-exposure data laws.

    It is exactly zero for any p_first and p_second because both laws put unit
    mass on the same null observation sequence.
    """

    no_exposure_observation_probability(
        closure_probability=p_first,
        observations=observations,
    )
    no_exposure_observation_probability(
        closure_probability=p_second,
        observations=observations,
    )
    return 0.0


def no_exposure_identifiability_bound(
    *,
    p_lower: float = 0.0,
    p_upper: float = 1.0,
) -> NoExposureIdentifiabilityResult:
    """Return the exact minimax absolute-error bound without exposure.

    Because the observed data are identical for every p in the interval, any
    estimator must return the same value for all parameter values. The constant
    minimizing the maximum absolute error is the interval midpoint, with
    minimax error equal to half the interval width.
    """

    if (
        not isfinite(p_lower)
        or not isfinite(p_upper)
        or not 0.0 <= p_lower <= p_upper <= 1.0
    ):
        raise ValueError("require 0 <= p_lower <= p_upper <= 1")
    midpoint = 0.5 * (p_lower + p_upper)
    return NoExposureIdentifiabilityResult(
        p_lower=p_lower,
        p_upper=p_upper,
        observation_law_depends_on_p=False,
        identifiable=p_lower == p_upper,
        minimax_absolute_error=0.5 * (p_upper - p_lower),
        midpoint_estimate=midpoint,
    )
