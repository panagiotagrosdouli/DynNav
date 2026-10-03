"""Exact finite-horizon belief-policy reference for tiny V4 worlds.

This module is intentionally exponential and limited to small hazard sets. It
exists to measure the approximation introduced by the receding-horizon
predictive-belief planner; it is not a scalable DynNav planning algorithm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from dynnav.activation_belief import ActivationBelief, expected_safe_return_probability
from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap


BeliefKey = tuple[tuple[tuple[int, ...], float], ...]


@dataclass(frozen=True)
class ExactBeliefPolicyConfig:
    horizon: int = 12
    step_cost: float = 1.0
    recoverability_weight: float = 8.0
    belief_round_digits: int = 12
    max_hazards: int = 3
    terminal_failure_cost: float = 1_000_000.0

    def validate(self) -> None:
        if self.horizon < 0:
            raise ValueError("horizon must be non-negative")
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")
        if self.belief_round_digits < 6:
            raise ValueError("belief_round_digits must be at least 6")
        if self.max_hazards < 0:
            raise ValueError("max_hazards must be non-negative")
        if self.terminal_failure_cost <= 0.0:
            raise ValueError("terminal_failure_cost must be positive")


@dataclass(frozen=True)
class ExactBeliefPolicyResult:
    success: bool
    first_action: GridCell | None
    value: float
    states_evaluated: int
    horizon: int


def _key(belief: ActivationBelief, *, digits: int) -> BeliefKey:
    return tuple(
        sorted(
            (
                tuple(sorted(active)),
                round(float(probability), digits),
            )
            for active, probability in belief.probability_by_active_set.items()
            if probability > 0.0
        )
    )


def _from_key(key: BeliefKey) -> ActivationBelief:
    raw = {
        frozenset(active): float(probability)
        for active, probability in key
    }
    total = sum(raw.values())
    if total <= 0.0:
        raise ValueError("belief key has zero total probability")
    return ActivationBelief(
        {active: probability / total for active, probability in raw.items()}
    )


def _trigger_index(
    model: CommitmentHazardModel,
    current: GridCell,
    neighbor: GridCell,
) -> int | None:
    matches = [
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger == (current, neighbor)
    ]
    if len(matches) > 1:
        raise ValueError("exact reference requires at most one hazard per transition")
    return matches[0] if matches else None


def _observation_branches(
    belief: ActivationBelief,
    hazard_index: int,
    *,
    sensitivity: float,
    specificity: float,
) -> tuple[tuple[float, ActivationBelief], ...]:
    armed_probability = belief.probability_armed(hazard_index)
    positive_probability = (
        sensitivity * armed_probability
        + (1.0 - specificity) * (1.0 - armed_probability)
    )
    branches: list[tuple[float, ActivationBelief]] = []
    for observed_armed, probability in (
        (True, positive_probability),
        (False, 1.0 - positive_probability),
    ):
        if probability <= 0.0:
            continue
        posterior = belief.condition_on_arming_observation(
            hazard_index,
            observed_armed=observed_armed,
            detection_sensitivity=sensitivity,
            detection_specificity=specificity,
        )
        branches.append((probability, posterior))
    return tuple(branches)


def exact_finite_horizon_belief_policy(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell],
    hazard_model: CommitmentHazardModel,
    arming_probabilities: tuple[float, ...],
    detection_sensitivities: tuple[float, ...],
    detection_specificities: tuple[float, ...],
    initial_belief: ActivationBelief | None = None,
    config: ExactBeliefPolicyConfig | None = None,
) -> ExactBeliefPolicyResult:
    """Solve a small finite-horizon observation-contingent policy exactly.

    The executed-action objective is the expected sum of geometric step cost and
    post-observation safe-return fragility. Goal states terminate with zero
    additional cost. Failure to reach the goal by horizon receives the declared
    terminal penalty.
    """

    cfg = config or ExactBeliefPolicyConfig()
    cfg.validate()
    grid.validate()
    hazard_model.validate(grid)

    n = len(hazard_model.closures)
    if n > cfg.max_hazards:
        raise ValueError(
            f"exact belief policy limited to {cfg.max_hazards} hazards; got {n}"
        )
    for label, values in (
        ("arming_probabilities", arming_probabilities),
        ("detection_sensitivities", detection_sensitivities),
        ("detection_specificities", detection_specificities),
    ):
        if len(values) != n:
            raise ValueError(f"{label} must have one value per hazard")
        if any(not 0.0 <= float(value) <= 1.0 for value in values):
            raise ValueError(f"{label} values must be in [0, 1]")

    belief0 = initial_belief or ActivationBelief.certain_inactive()
    belief0.validate(n)
    safe = set(safe_cells)
    if not safe:
        raise ValueError("safe_cells cannot be empty")

    beliefs: dict[BeliefKey, ActivationBelief] = {}
    initial_key = _key(belief0, digits=cfg.belief_round_digits)
    beliefs[initial_key] = belief0
    states_evaluated = 0

    def register(belief: ActivationBelief) -> BeliefKey:
        key = _key(belief, digits=cfg.belief_round_digits)
        beliefs.setdefault(key, belief)
        return key

    @lru_cache(maxsize=None)
    def value(cell: GridCell, belief_key: BeliefKey, remaining: int) -> float:
        nonlocal states_evaluated
        states_evaluated += 1
        if cell == goal:
            return 0.0
        if remaining <= 0:
            return cfg.terminal_failure_cost

        belief = beliefs.get(belief_key)
        if belief is None:
            belief = _from_key(belief_key)
            beliefs[belief_key] = belief

        best = math.inf
        for neighbor in grid.neighbors4(cell):
            hazard_index = _trigger_index(hazard_model, cell, neighbor)
            if hazard_index is None:
                branches = ((1.0, belief),)
            else:
                predicted = belief.predict_after_trigger_execution(
                    hazard_index,
                    arming_probability=float(arming_probabilities[hazard_index]),
                )
                branches = _observation_branches(
                    predicted,
                    hazard_index,
                    sensitivity=float(detection_sensitivities[hazard_index]),
                    specificity=float(detection_specificities[hazard_index]),
                )

            expected = 0.0
            for observation_probability, posterior in branches:
                posterior_key = register(posterior)
                return_probability = expected_safe_return_probability(
                    grid,
                    neighbor,
                    safe,
                    hazard_model,
                    posterior,
                    max_hazard_cells=max(16, n),
                )
                stage = (
                    cfg.step_cost
                    + cfg.recoverability_weight * (1.0 - return_probability)
                )
                future = value(neighbor, posterior_key, remaining - 1)
                expected += observation_probability * (stage + future)
            best = min(best, expected)
        return best

    if start == goal:
        return ExactBeliefPolicyResult(True, None, 0.0, 1, cfg.horizon)

    best_action: GridCell | None = None
    best_value = math.inf
    belief = belief0
    for neighbor in grid.neighbors4(start):
        hazard_index = _trigger_index(hazard_model, start, neighbor)
        if hazard_index is None:
            branches = ((1.0, belief),)
        else:
            predicted = belief.predict_after_trigger_execution(
                hazard_index,
                arming_probability=float(arming_probabilities[hazard_index]),
            )
            branches = _observation_branches(
                predicted,
                hazard_index,
                sensitivity=float(detection_sensitivities[hazard_index]),
                specificity=float(detection_specificities[hazard_index]),
            )

        expected = 0.0
        for observation_probability, posterior in branches:
            posterior_key = register(posterior)
            return_probability = expected_safe_return_probability(
                grid,
                neighbor,
                safe,
                hazard_model,
                posterior,
                max_hazard_cells=max(16, n),
            )
            stage = (
                cfg.step_cost
                + cfg.recoverability_weight * (1.0 - return_probability)
            )
            expected += observation_probability * (
                stage + value(neighbor, posterior_key, cfg.horizon - 1)
            )
        if expected < best_value:
            best_value = expected
            best_action = neighbor

    success = best_action is not None and best_value < cfg.terminal_failure_cost
    return ExactBeliefPolicyResult(
        success=success,
        first_action=best_action,
        value=best_value,
        states_evaluated=states_evaluated,
        horizon=cfg.horizon,
    )
