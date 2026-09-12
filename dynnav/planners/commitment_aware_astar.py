"""Augmented-state A* for history-conditioned future closure hazards."""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass
from enum import Enum

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability

AugmentedState = tuple[GridCell, frozenset[int]]


class CommitmentPlannerMode(str, Enum):
    SHORTEST = "shortest"
    HISTORY_AWARE = "history_aware"


@dataclass(frozen=True)
class CommitmentAwareAStarConfig:
    step_cost: float = 1.0
    recoverability_weight: float = 4.0
    heuristic_weight: float = 1.0
    max_hazard_cells: int = 16

    def validate(self) -> None:
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")
        if self.heuristic_weight < 0.0:
            raise ValueError("heuristic_weight must be non-negative")
        if self.max_hazard_cells < 0:
            raise ValueError("max_hazard_cells must be non-negative")


@dataclass(frozen=True)
class CommitmentAwareAStarResult:
    path: tuple[GridCell, ...]
    success: bool
    cost: float
    geometric_length: int
    nodes_expanded: int
    planning_time_ms: float
    final_return_probability: float
    minimum_return_probability: float
    cumulative_return_fragility: float
    activated_closure_count: int
    mode: CommitmentPlannerMode


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


def _hazard_from_active(
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


def _return_probability(
    grid: GridMap,
    cell: GridCell,
    safe_cells: set[GridCell],
    model: CommitmentHazardModel,
    active: frozenset[int],
    max_hazard_cells: int,
) -> float:
    hazard = _hazard_from_active(model, active, cell)
    return exact_safe_return_probability(
        grid,
        cell,
        safe_cells,
        hazard,
        max_hazard_cells=max_hazard_cells,
    )


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


def commitment_aware_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    mode: CommitmentPlannerMode = CommitmentPlannerMode.HISTORY_AWARE,
    config: CommitmentAwareAStarConfig | None = None,
) -> CommitmentAwareAStarResult:
    """Plan over position plus activated closure history.

    The history-aware objective penalizes ``1 - P(return to safe set)`` after
    each transition, where the probability is evaluated from the closure events
    activated by the path prefix. The shortest baseline searches the same
    augmented transition system but ignores the recoverability penalty.

    Exact enumeration is intentionally used only for small controlled worlds;
    this implementation is a scientific oracle/baseline, not a claimed scalable
    deployment planner. ``max_hazard_cells`` constrains the active hazard set
    passed to the exact oracle, not the number of possible triggers declared in
    the model.
    """

    grid.validate()
    cfg = config or CommitmentAwareAStarConfig()
    cfg.validate()
    safe = set(safe_cells or {start})
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return CommitmentAwareAStarResult(
            (), False, float("inf"), 0, 0, 0.0, 0.0, 0.0, float("inf"), 0, mode
        )

    t0 = time.perf_counter()
    initial: AugmentedState = (start, frozenset())
    frontier: list[tuple[float, int, AugmentedState]] = [(0.0, 0, initial)]
    costs: dict[AugmentedState, float] = {initial: 0.0}
    parents: dict[AugmentedState, AugmentedState] = {}
    counter = 0
    nodes_expanded = 0

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, active = state
        nodes_expanded += 1
        if cell == goal:
            states = _reconstruct_states(parents, state)
            path = tuple(item[0] for item in states)
            return_probabilities = [
                _return_probability(
                    grid,
                    item_cell,
                    safe,
                    model,
                    item_active,
                    cfg.max_hazard_cells,
                )
                for item_cell, item_active in states
            ]
            return CommitmentAwareAStarResult(
                path=path,
                success=True,
                cost=costs[state],
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=nodes_expanded,
                planning_time_ms=(time.perf_counter() - t0) * 1000.0,
                final_return_probability=return_probabilities[-1],
                minimum_return_probability=min(return_probabilities),
                cumulative_return_fragility=sum(
                    1.0 - probability for probability in return_probabilities[1:]
                ),
                activated_closure_count=len(active),
                mode=mode,
            )

        for neighbor in grid.neighbors4(cell):
            next_active = _activated_after_transition(model, cell, neighbor, active)
            next_state: AugmentedState = (neighbor, next_active)
            transition = cfg.step_cost
            if mode is CommitmentPlannerMode.HISTORY_AWARE:
                probability = _return_probability(
                    grid,
                    neighbor,
                    safe,
                    model,
                    next_active,
                    cfg.max_hazard_cells,
                )
                transition += cfg.recoverability_weight * (1.0 - probability)
            new_cost = costs[state] + transition
            if new_cost < costs.get(next_state, float("inf")):
                costs[next_state] = new_cost
                parents[next_state] = state
                counter += 1
                priority = new_cost + cfg.heuristic_weight * cfg.step_cost * manhattan(
                    neighbor, goal
                )
                heapq.heappush(frontier, (priority, counter, next_state))

    return CommitmentAwareAStarResult(
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
