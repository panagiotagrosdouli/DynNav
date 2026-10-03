"""Beliefs over latent arming of action-triggered topology hazards.

The V4 research model separates four events:
1. a trigger transition is known to have been executed;
2. that action may arm a latent environmental hazard;
3. the robot receives a noisy observation of the armed state; and
4. an armed hazard may later realize a topology closure.

This module keeps exact categorical beliefs for small hazard sets. It is a
reference implementation for falsification and validation, not a scalable
general POMDP solver.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose, isfinite
from types import MappingProxyType

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability


def _unit_interval(name: str, value: float) -> float:
    value = float(value)
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


@dataclass(frozen=True)
class ActivationBelief:
    """Categorical belief over the set of armed hazard indices."""

    probability_by_active_set: Mapping[frozenset[int], float]

    def __post_init__(self) -> None:
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
    def certain_inactive(cls) -> "ActivationBelief":
        """Return the prior before any hazard has been armed."""
        return cls({frozenset(): 1.0})

    @classmethod
    def certain_active(cls, active: frozenset[int] | set[int]) -> "ActivationBelief":
        """Return a point belief over one armed-hazard set."""
        return cls({frozenset(active): 1.0})

    def _validation_count(self, hazard_index: int) -> int:
        if hazard_index < 0:
            raise ValueError("hazard_index must be non-negative")
        highest_active_index = max(
            (index for active in self.probability_by_active_set for index in active),
            default=-1,
        )
        return max(hazard_index, highest_active_index) + 1

    def predict_after_trigger_execution(
        self,
        hazard_index: int,
        *,
        arming_probability: float,
    ) -> "ActivationBelief":
        """Propagate after a known trigger execution, before observation."""
        self.validate(self._validation_count(hazard_index))
        q = _unit_interval("arming_probability", arming_probability)

        predicted: dict[frozenset[int], float] = {}
        for active, prior in self.probability_by_active_set.items():
            if hazard_index in active:
                predicted[active] = predicted.get(active, 0.0) + prior
                continue

            inactive_probability = prior * (1.0 - q)
            active_probability = prior * q
            if inactive_probability:
                predicted[active] = predicted.get(active, 0.0) + inactive_probability
            if active_probability:
                armed = active | {hazard_index}
                predicted[armed] = predicted.get(armed, 0.0) + active_probability

        return ActivationBelief(predicted)

    def condition_on_arming_observation(
        self,
        hazard_index: int,
        *,
        observed_armed: bool,
        detection_sensitivity: float,
        detection_specificity: float,
    ) -> "ActivationBelief":
        """Condition a predictive belief on one noisy arming observation."""
        self.validate(self._validation_count(hazard_index))
        sensitivity = _unit_interval("detection_sensitivity", detection_sensitivity)
        specificity = _unit_interval("detection_specificity", detection_specificity)

        unnormalized: dict[frozenset[int], float] = {}
        for active, prior in self.probability_by_active_set.items():
            is_armed = hazard_index in active
            if is_armed:
                likelihood = sensitivity if observed_armed else 1.0 - sensitivity
            else:
                likelihood = 1.0 - specificity if observed_armed else specificity
            joint = prior * likelihood
            if joint > 0.0:
                unnormalized[active] = joint

        evidence_probability = sum(unnormalized.values())
        if evidence_probability == 0.0:
            raise ValueError("observation has zero probability under the supplied model")

        return ActivationBelief(
            {
                active: probability / evidence_probability
                for active, probability in unnormalized.items()
            }
        )

    def update_after_trigger_execution(
        self,
        hazard_index: int,
        *,
        arming_probability: float,
        observed_armed: bool,
        detection_sensitivity: float,
        detection_specificity: float,
    ) -> "ActivationBelief":
        """Exact Bayes update for known trigger execution and latent arming."""
        return self.predict_after_trigger_execution(
            hazard_index,
            arming_probability=arming_probability,
        ).condition_on_arming_observation(
            hazard_index,
            observed_armed=observed_armed,
            detection_sensitivity=detection_sensitivity,
            detection_specificity=detection_specificity,
        )

    def update_after_trigger_attempt(
        self,
        hazard_index: int,
        *,
        execution_probability: float,
        observed_crossing: bool,
        detection_sensitivity: float,
        detection_specificity: float,
    ) -> "ActivationBelief":
        """Compatibility wrapper for the provisional noisy-crossing model.

        New V4 work should use update_after_trigger_execution, where geometric
        trigger execution is known and arming_probability captures uncertainty
        in the latent environmental response.
        """
        return self.update_after_trigger_execution(
            hazard_index,
            arming_probability=execution_probability,
            observed_armed=observed_crossing,
            detection_sensitivity=detection_sensitivity,
            detection_specificity=detection_specificity,
        )

    def probability_armed(self, hazard_index: int) -> float:
        """Return the marginal posterior probability that one hazard is armed."""
        self.validate(self._validation_count(hazard_index))
        return sum(
            probability
            for active, probability in self.probability_by_active_set.items()
            if hazard_index in active
        )

    def entropy_bits(self) -> float:
        """Return Shannon entropy of the categorical armed-set belief in bits."""
        import math
        return -sum(
            probability * math.log2(probability)
            for probability in self.probability_by_active_set.values()
            if probability > 0.0
        )


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

    This mixes the existing exact independent-closure oracle over possible
    armed-hazard sets. It is exact only under that closure model.
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
                    "armed hazards assign conflicting probabilities "
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
