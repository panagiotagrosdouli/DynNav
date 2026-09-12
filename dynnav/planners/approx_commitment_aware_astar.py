"""Scalable augmented-state A* for action-triggered return hazards.

Unlike the exact commitment-aware oracle planner, this module does not enumerate
all future closure realizations. It maintains the same activated-hazard history
state but evaluates return reliability with conservative path-reliability
estimators.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass
from enum import Enum

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.recoverability_belief import TopologyHazardBelief
from dynnav.recoverability_estimation import (
    most_reliable_return_path,
    two_hazard_disjoint_return_paths,
)

AugmentedState = tuple[GridCell, frozenset[int]]


class ApproxCommitmentMode(str, Enum):
    SINGLE_RETURN = "single_return"
    REDUNDANT_RETURN = "redundant_return"


@dataclass(frozen=True)
class ApproxCommitmentAStarConfig:
    step_cost: float = 1.0
    recoverability_weight: float = 4.0
    heuristic_weight: float = 1.0

    def validate(self) -> None:
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")
        if self.heuristic_weight < 0.0:
            raise ValueError("heuristic_weight must be non-negative")


@dataclass(frozen=True)
class ApproxCommitmentAStarResult:
    path: tuple[GridCell, ...]
    success: bool
    cost: float
    geometric_length: int
    nodes_expanded: int
    planning_time_ms: float
    final_estimated_return_probability: float
    minimum_estimated_return_probability: float
    cumulative_estimated_return_fragility: float
    activated_closure_count: int
    mode: ApproxCommitmentMode


def _activated_after_transition(
    model: CommitmentHazardModel,
    current: GridCell,
    neighbor: GridCell,
    active: frozenset[int],
) -> frozenset[int]:
    additions = {
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger == (current, neighbor)
    }
    return active | frozenset(additions)


def _active_hazard(
    model: CommitmentHazardModel,
    active: frozenset[int],
    current: GridCell,
) -> TopologyHazardBelief:
    probabilities: dict[GridCell, float] = {}
    for index in active:
        closure = model.closures[index]
        if closure.closure_cell == current:
            continue
        existing = probabilities.get(closure.closure_cell)
        if existing is not None and existing != closure.closure_probability:
            raise ValueError(
                "active commitment hazards assign conflicting probabilities "
                f"to {closure.closure_cell}"
            )
        probabilities[closure.closure_cell] = closure.closure_probability
    return TopologyHazardBelief(probabilities)


def _estimated_return_probability(
    mode: ApproxCommitmentMode,
    grid: GridMap,
    cell: GridCell,
    safe_cells: set[GridCell],
    model: CommitmentHazardModel,
    active: frozenset[int],
) -> float:
    hazard = _active_hazard(model, active, cell)
    if mode is ApproxCommitmentMode.SINGLE_RETURN:
        return most_reliable_return_path(grid, cell, safe_cells, hazard).probability
    return two_hazard_disjoint_return_paths(grid, cell, safe_cells, hazard).probability


def _reconstruct_states(
    parents: dict[AugmentedState, AugmentedState],
    state: AugmentedState,
) -> tuple[AugmentedState, ...]:
    states = [state]
    while state in parents:
        state = parents[state]
        states.append(state)
    states.reverse()
    return tuple(states)


def approx_commitment_aware_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    mode: ApproxCommitmentMode = ApproxCommitmentMode.REDUNDANT_RETURN,
    config: ApproxCommitmentAStarConfig | None = None,
) -> ApproxCommitmentAStarResult:
    """Plan in position×activated-history space without exact outcome enumeration.

    The planner retains action history only through the set of closure events
    that have been activated. Return reliability is then approximated using one
    or two hazard-disjoint paths. This avoids the exact oracle's enumeration of
    all closure realizations while preserving action-conditioned topology state.
    """

    grid.validate()
    cfg = config or ApproxCommitmentAStarConfig()
    cfg.validate()
    safe = set(safe_cells or {start})
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return ApproxCommitmentAStarResult(
            (), False, float("inf"), 0, 0, 0.0, 0.0, 0.0, float("inf"), 0, mode
        )

    t0 = time.perf_counter()
    initial: AugmentedState = (start, frozenset())
    frontier: list[tuple[float, int, AugmentedState]] = [(0.0, 0, initial)]
    costs: dict[AugmentedState, float] = {initial: 0.0}
    parents: dict[AugmentedState, AugmentedState] = {}
    estimate_cache: dict[AugmentedState, float] = {}
    counter = 0
    nodes_expanded = 0

    def estimate(state: AugmentedState) -> float:
        if state not in estimate_cache:
            cell, active = state
            estimate_cache[state] = _estimated_return_probability(
                mode, grid, cell, safe, model, active
            )
        return estimate_cache[state]

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, active = state
        nodes_expanded += 1
        if cell == goal:
            states = _reconstruct_states(parents, state)
            path = tuple(item[0] for item in states)
            values = [estimate(item) for item in states]
            return ApproxCommitmentAStarResult(
                path=path,
                success=True,
                cost=costs[state],
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=nodes_expanded,
                planning_time_ms=(time.perf_counter() - t0) * 1000.0,
                final_estimated_return_probability=values[-1],
                minimum_estimated_return_probability=min(values),
                cumulative_estimated_return_fragility=sum(1.0 - value for value in values[1:]),
                activated_closure_count=len(active),
                mode=mode,
            )

        for neighbor in grid.neighbors4(cell):
            next_active = _activated_after_transition(model, cell, neighbor, active)
            next_state: AugmentedState = (neighbor, next_active)
            probability = estimate(next_state)
            transition = cfg.step_cost + cfg.recoverability_weight * (1.0 - probability)
            new_cost = costs[state] + transition
            if new_cost < costs.get(next_state, float("inf")):
                costs[next_state] = new_cost
                parents[next_state] = state
                counter += 1
                priority = new_cost + cfg.heuristic_weight * cfg.step_cost * manhattan(
                    neighbor, goal
                )
                heapq.heappush(frontier, (priority, counter, next_state))

    return ApproxCommitmentAStarResult(
        (),
        False,
        float("inf"),
        0,
        nodes_expanded,
        (time.perf_counter() - t0) * 1000.0,
        0.0,
        0.0,
        float("inf"),
        0,
        mode,
    )
