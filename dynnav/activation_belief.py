"""Exact beliefs over uncertain execution of action-triggered hazards.

The module separates three events that a deterministic history model tends to
collapse: an attempted edge is actually crossed, that crossing is observed
through a noisy detector, and a future topology closure realizes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose, isfinite
from types import MappingProxyType

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability


@dataclass(frozen=True)
class ActivationBelief:
    """Categorical belief over the set of activated hazard indices."""

    probability_by_active_set: Mapping[frozenset[int], float]

    def __post_init__(self) -> None:
        # A frozen dataclass alone does not protect a caller-owned dict from
        # mutation. Copy the support so a validated belief stays stable.
        normalized = {
            frozenset(active): float(probability)
            for active, probability in self.probability_by_active_set.items()
        }
        object.__setattr__(self, "probability_by_active_set", MappingProxyType(normalized))

    def validate(self, hazard_count: int) -> None:
        if hazard_count < 0:
            raise ValueError("hazard_count must be non-negative")
        if not self.probability_by_active_set:
            raise ValueError("activation belief cannot be empty")
        total = 0.0
        for active, probability in self.probability_by_active_set.items():
            if any(not isinstance(index, int) for index in active):
                raise ValueError("active hazard indices must be integers")
            if any(index < 0 or index >= hazard_count for index in active):
                raise ValueError(f"active hazard indices out of range: {sorted(active)}")
            if not isfinite(probability) or probability < 0.0 or probability > 1.0:
                raise ValueError(f"belief probability must be in [0, 1], got {probability}")
            total += probability
        if not isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"activation belief must sum to 1, got {total}")

    @classmethod
    def certain_inactive(cls) -> ActivationBelief:
        """Return the prior before any trigger transition has been attempted."""

        return cls({frozenset(): 1.0})

    def update_after_trigger_attempt(
        self,
        hazard_index: int,
        *,
        execution_probability: float,
        observed_crossing: bool,
        detection_sensitivity: float,
        detection_specificity: float,
    ) -> ActivationBelief:
        """Apply one noisy executed-edge observation with an exact Bayes update.

        The commanded trigger transition is physically crossed with probability
        ``execution_probability``. Crossing activates the hazard. The detector
        reports crossing with the declared sensitivity and specificity. The
        returned distribution is over the post-transition active sets.
        """

        if hazard_index < 0:
            raise ValueError("hazard_index must be non-negative")
        highest_active_index = max(
            (index for active in self.probability_by_active_set for index in active),
            default=-1,
        )
        self.validate(max(hazard_index, highest_active_index) + 1)
        for name, value in (
            ("execution_probability", execution_probability),
            ("detection_sensitivity", detection_sensitivity),
            ("detection_specificity", detection_specificity),
        ):
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")

        unnormalized: dict[frozenset[int], float] = {}
        for active, prior in self.probability_by_active_set.items():
            for crossed, crossing_probability in (
                (False, 1.0 - execution_probability),
                (True, execution_probability),
            ):
                if crossing_probability == 0.0:
                    continue
                next_active = active | {hazard_index} if crossed else active
                observation_probability = (
                    detection_sensitivity if observed_crossing else 1.0 - detection_sensitivity
                ) if crossed else (
                    1.0 - detection_specificity if observed_crossing else detection_specificity
                )
                joint = prior * crossing_probability * observation_probability
                if joint > 0.0:
                    unnormalized[next_active] = unnormalized.get(next_active, 0.0) + joint

        evidence_probability = sum(unnormalized.values())
        if evidence_probability == 0.0:
            raise ValueError("observation has zero probability under the supplied model")
        posterior = {
            active: probability / evidence_probability
            for active, probability in unnormalized.items()
        }
        return ActivationBelief(posterior)


def expected_safe_return_probability(
    grid: GridMap,
    current: GridCell,
    safe_cells: set[GridCell],
    hazard_model: CommitmentHazardModel,
    activation_belief: ActivationBelief,
    *,
    max_hazard_cells: int = 16,
) -> float:
    """Return posterior-predictive safe-return probability exactly.

    This is the law-of-total-probability mixture of the existing exact
    independent-closure oracle over possible active-hazard sets. The maximum
    exact hazard count applies separately to each belief hypothesis.
    """

    hazard_model.validate(grid)
    activation_belief.validate(len(hazard_model.closures))
    total = 0.0
    for active, state_probability in activation_belief.probability_by_active_set.items():
        closure_probability: dict[GridCell, float] = {}
        for index in active:
            closure = hazard_model.closures[index]
            if closure.closure_cell == current:
                continue
            existing = closure_probability.get(closure.closure_cell)
            if existing is not None and existing != closure.closure_probability:
                raise ValueError(
                    "active hazards assign conflicting probabilities "
                    f"to closure cell {closure.closure_cell}"
                )
            closure_probability[closure.closure_cell] = closure.closure_probability
        state_return_probability = exact_safe_return_probability(
            grid,
            current,
            safe_cells,
            TopologyHazardBelief(closure_probability),
            max_hazard_cells=max_hazard_cells,
        )
        total += state_probability * state_return_probability
    return min(1.0, max(0.0, total))
