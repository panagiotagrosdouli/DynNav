"""Finite-sample ambiguity sets for future topology closures.

The estimator converts matched binary closure observations into simultaneous
Clopper-Pearson confidence intervals for marginal and optional pairwise joint
closure probabilities.  A Bonferroni correction is used across all retained
constraints so the family-wise confidence level is explicit.

This module estimates statistical ambiguity; it does not assume that the
resulting confidence set is a calibrated deployment-safety certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import comb

from scipy.stats import beta as beta_distribution

from dynnav.distributional_recoverability import (
    PairwiseClosureConstraint,
    ProbabilityInterval,
    TopologyAmbiguitySet,
)
from dynnav.planners.grid_map import GridCell


@dataclass(frozen=True)
class ClosureObservation:
    closed_cells: frozenset[GridCell]


@dataclass(frozen=True)
class EmpiricalAmbiguityFit:
    ambiguity: TopologyAmbiguitySet
    sample_size: int
    family_confidence: float
    marginal_estimates: dict[GridCell, float]
    pairwise_estimates: dict[tuple[GridCell, GridCell], float]


def _clopper_pearson_interval(
    successes: int,
    trials: int,
    *,
    alpha: float,
) -> ProbabilityInterval:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must lie in [0, trials]")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")

    lower = (
        0.0
        if successes == 0
        else float(
            beta_distribution.ppf(
                alpha / 2.0,
                successes,
                trials - successes + 1,
            )
        )
    )
    upper = (
        1.0
        if successes == trials
        else float(
            beta_distribution.ppf(
                1.0 - alpha / 2.0,
                successes + 1,
                trials - successes,
            )
        )
    )
    return ProbabilityInterval(lower=lower, upper=upper)


def fit_empirical_topology_ambiguity(
    observations: tuple[ClosureObservation, ...] | list[ClosureObservation],
    hazard_cells: tuple[GridCell, ...] | list[GridCell],
    *,
    family_confidence: float = 0.95,
    include_pairwise: bool = True,
) -> EmpiricalAmbiguityFit:
    """Fit simultaneous marginal/pairwise probability intervals.

    Every observation is a matched realization of all listed hazard cells.
    Pairwise constraints therefore estimate P(C_i=1 AND C_j=1), not a
    correlation coefficient.
    """

    if not observations:
        raise ValueError("at least one closure observation is required")
    cells = tuple(hazard_cells)
    if not cells:
        raise ValueError("hazard_cells cannot be empty")
    if len(set(cells)) != len(cells):
        raise ValueError("hazard_cells must be unique")
    if not 0.0 < family_confidence < 1.0:
        raise ValueError("family_confidence must be in (0, 1)")

    allowed = set(cells)
    for observation in observations:
        unknown = observation.closed_cells - allowed
        if unknown:
            raise ValueError(f"observation contains unknown hazard cells: {sorted(unknown)}")

    pair_count = comb(len(cells), 2) if include_pairwise else 0
    constraint_count = len(cells) + pair_count
    family_alpha = 1.0 - family_confidence
    per_constraint_alpha = family_alpha / constraint_count
    n = len(observations)

    marginals: dict[GridCell, ProbabilityInterval] = {}
    marginal_estimates: dict[GridCell, float] = {}
    for cell in cells:
        count = sum(cell in observation.closed_cells for observation in observations)
        marginals[cell] = _clopper_pearson_interval(
            count,
            n,
            alpha=per_constraint_alpha,
        )
        marginal_estimates[cell] = count / n

    pairwise_constraints: list[PairwiseClosureConstraint] = []
    pairwise_estimates: dict[tuple[GridCell, GridCell], float] = {}
    if include_pairwise:
        for first, second in combinations(cells, 2):
            count = sum(
                first in observation.closed_cells and second in observation.closed_cells
                for observation in observations
            )
            interval = _clopper_pearson_interval(
                count,
                n,
                alpha=per_constraint_alpha,
            )
            pairwise_constraints.append(
                PairwiseClosureConstraint(first, second, interval)
            )
            pairwise_estimates[(first, second)] = count / n

    return EmpiricalAmbiguityFit(
        ambiguity=TopologyAmbiguitySet(
            marginals=marginals,
            pairwise=tuple(pairwise_constraints),
        ),
        sample_size=n,
        family_confidence=family_confidence,
        marginal_estimates=marginal_estimates,
        pairwise_estimates=pairwise_estimates,
    )
