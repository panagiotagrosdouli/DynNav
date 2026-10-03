"""Predictive-belief A* for partially observed action-induced topology hazards.

This is the V4 reference planner. It propagates the current posterior belief
through future trigger executions while marginalizing observations that have
not happened yet. The caller executes a transition, receives an observation,
updates the posterior with ActivationBelief.update_after_trigger_execution,
and replans.

It is therefore a receding-horizon belief-conditioned planner, not an optimal
POMDP policy solver.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from dynnav.activation_belief import ActivationBelief, expected_safe_return_probability
from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap, manhattan

BeliefKey = tuple[tuple[tuple[int, ...], float], ...]
BeliefState = tuple[GridCell, BeliefKey]


@dataclass(frozen=True)
class BeliefCommitmentAStarConfig:
    step_cost: float = 1.0
    recoverability_weight: float = 8.0
    heuristic_weight: float = 1.0
    max_hazard_cells: int = 16
    belief_round_digits: int = 15
    minimum_return_probability: float | None = None

    def validate(self) -> None:
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")
        if self.heuristic_weight < 0.0:
            raise ValueError("heuristic_weight must be non-negative")
        if self.max_hazard_cells < 0:
            raise ValueError("max_hazard_cells must be non-negative")
        if self.belief_round_digits < 6:
            raise ValueError("belief_round_digits must be at least 6")
        if (
            self.minimum_return_probability is not None
            and not 0.0 <= self.minimum_return_probability <= 1.0
        ):
            raise ValueError("minimum_return_probability must be in [0, 1]")


@dataclass(frozen=True)
class BeliefCommitmentAStarResult:
    path: tuple[GridCell, ...]
    success: bool
    cost: float
    geometric_length: int
    nodes_expanded: int
    return_oracle_calls: int
    planning_time_ms: float
    final_predicted_return_probability: float
    minimum_predicted_return_probability: float
    final_belief_support_size: int
    final_belief_entropy_bits: float
    final_expected_armed_hazards: float


def _belief_key(belief: ActivationBelief, *, digits: int) -> BeliefKey:
    """Return a deterministic key for an exact small-support belief."""

    items = []
    for active, probability in belief.probability_by_active_set.items():
        if probability <= 0.0:
            continue
        items.append((tuple(sorted(active)), round(float(probability), digits)))
    return tuple(sorted(items))


def _expected_armed_count(belief: ActivationBelief) -> float:
    return sum(
        probability * len(active)
        for active, probability in belief.probability_by_active_set.items()
    )


def _reconstruct_states(
    parents: dict[BeliefState, BeliefState],
    state: BeliefState,
) -> tuple[BeliefState, ...]:
    states = [state]
    while state in parents:
        state = parents[state]
        states.append(state)
    states.reverse()
    return tuple(states)


def _validate_arming_probabilities(
    model: CommitmentHazardModel,
    arming_probabilities: tuple[float, ...],
) -> None:
    if len(arming_probabilities) != len(model.closures):
        raise ValueError(
            "arming_probabilities must have one value per commitment hazard"
        )
    for index, probability in enumerate(arming_probabilities):
        if not 0.0 <= float(probability) <= 1.0:
            raise ValueError(
                f"arming probability at index {index} must be in [0, 1]"
            )


def _predict_after_transition(
    model: CommitmentHazardModel,
    belief: ActivationBelief,
    current: GridCell,
    neighbor: GridCell,
    arming_probabilities: tuple[float, ...],
) -> ActivationBelief:
    predicted = belief
    for index, closure in enumerate(model.closures):
        if closure.trigger == (current, neighbor):
            predicted = predicted.predict_after_trigger_execution(
                index,
                arming_probability=float(arming_probabilities[index]),
            )
    return predicted


def belief_commitment_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    arming_probabilities: tuple[float, ...] | None = None,
    initial_belief: ActivationBelief | None = None,
    config: BeliefCommitmentAStarConfig | None = None,
) -> BeliefCommitmentAStarResult:
    """Plan using posterior-predictive safe-return reliability.

    Future trigger transitions propagate the latent arming belief, but the
    search does not branch on future observations. After one real transition,
    the caller should condition on the actual detector observation and replan.
    """

    grid.validate()
    cfg = config or BeliefCommitmentAStarConfig()
    cfg.validate()
    safe = set(safe_cells) if safe_cells is not None else {start}
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)

    q = (
        tuple(1.0 for _ in model.closures)
        if arming_probabilities is None
        else tuple(float(value) for value in arming_probabilities)
    )
    _validate_arming_probabilities(model, q)

    belief0 = initial_belief or ActivationBelief.certain_inactive()
    belief0.validate(len(model.closures))

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return BeliefCommitmentAStarResult(
            (), False, float("inf"), 0, 0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0
        )

    initial_key = _belief_key(belief0, digits=cfg.belief_round_digits)
    initial: BeliefState = (start, initial_key)
    beliefs: dict[BeliefKey, ActivationBelief] = {initial_key: belief0}

    t0 = time.perf_counter()
    frontier: list[tuple[float, int, BeliefState]] = [(0.0, 0, initial)]
    costs: dict[BeliefState, float] = {initial: 0.0}
    parents: dict[BeliefState, BeliefState] = {}
    return_cache: dict[BeliefState, float] = {}
    counter = 0
    nodes_expanded = 0

    def return_probability(state: BeliefState) -> float:
        if state not in return_cache:
            cell, key = state
            return_cache[state] = expected_safe_return_probability(
                grid,
                cell,
                safe,
                model,
                beliefs[key],
                max_hazard_cells=cfg.max_hazard_cells,
            )
        return return_cache[state]

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, belief_key = state
        nodes_expanded += 1

        if cell == goal:
            planning_time_ms = (time.perf_counter() - t0) * 1000.0
            states = _reconstruct_states(parents, state)
            path = tuple(item[0] for item in states)
            probabilities = [return_probability(item) for item in states]
            final_belief = beliefs[states[-1][1]]
            return BeliefCommitmentAStarResult(
                path=path,
                success=True,
                cost=costs[state],
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=nodes_expanded,
                return_oracle_calls=len(return_cache),
                planning_time_ms=planning_time_ms,
                final_predicted_return_probability=probabilities[-1],
                minimum_predicted_return_probability=min(probabilities),
                final_belief_support_size=len(
                    final_belief.probability_by_active_set
                ),
                final_belief_entropy_bits=final_belief.entropy_bits(),
                final_expected_armed_hazards=_expected_armed_count(final_belief),
            )

        belief = beliefs[belief_key]
        for neighbor in grid.neighbors4(cell):
            next_belief = _predict_after_transition(
                model,
                belief,
                cell,
                neighbor,
                q,
            )
            next_key = _belief_key(
                next_belief,
                digits=cfg.belief_round_digits,
            )
            beliefs.setdefault(next_key, next_belief)
            next_state: BeliefState = (neighbor, next_key)

            probability = return_probability(next_state)
            if (
                cfg.minimum_return_probability is not None
                and probability < cfg.minimum_return_probability
            ):
                continue
            transition_cost = (
                cfg.step_cost
                + cfg.recoverability_weight * (1.0 - probability)
            )
            new_cost = costs[state] + transition_cost

            if new_cost < costs.get(next_state, float("inf")):
                costs[next_state] = new_cost
                parents[next_state] = state
                counter += 1
                priority = (
                    new_cost
                    + cfg.heuristic_weight
                    * cfg.step_cost
                    * manhattan(neighbor, goal)
                )
                heapq.heappush(frontier, (priority, counter, next_state))

    final_belief = belief0
    return BeliefCommitmentAStarResult(
        (),
        False,
        float("inf"),
        0,
        nodes_expanded,
        len(return_cache),
        (time.perf_counter() - t0) * 1000.0,
        0.0,
        0.0,
        len(final_belief.probability_by_active_set),
        final_belief.entropy_bits(),
        _expected_armed_count(final_belief),
    )
