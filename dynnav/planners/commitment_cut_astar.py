"""Augmented-state A* using a critical-return-cut recoverability approximation."""
from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.recoverability_belief import TopologyHazardBelief
from dynnav.recoverability_cut import critical_return_cut_upper_bound

AugmentedState = tuple[GridCell, frozenset[int]]


@dataclass(frozen=True)
class CommitmentCutAStarConfig:
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
class CommitmentCutAStarResult:
    path: tuple[GridCell, ...]
    success: bool
    cost: float
    geometric_length: int
    nodes_expanded: int
    planning_time_ms: float
    final_return_upper_bound: float
    minimum_return_upper_bound: float
    activated_closure_count: int


def _active_hazard(
    model: CommitmentHazardModel,
    active: frozenset[int],
    current: GridCell,
) -> TopologyHazardBelief:
    values: dict[GridCell, float] = {}
    for index in active:
        closure = model.closures[index]
        if closure.closure_cell == current:
            continue
        previous = values.get(closure.closure_cell)
        if previous is not None and previous != closure.closure_probability:
            raise ValueError("conflicting probabilities for active closure cell")
        values[closure.closure_cell] = closure.closure_probability
    return TopologyHazardBelief(values)


def _next_active(
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


def _reconstruct(
    parents: dict[AugmentedState, AugmentedState],
    state: AugmentedState,
) -> tuple[AugmentedState, ...]:
    values = [state]
    while state in parents:
        state = parents[state]
        values.append(state)
    values.reverse()
    return tuple(values)


def commitment_cut_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    config: CommitmentCutAStarConfig | None = None,
) -> CommitmentCutAStarResult:
    """Plan over position/history using the critical-cut return upper bound."""
    grid.validate()
    cfg = config or CommitmentCutAStarConfig()
    cfg.validate()
    safe = set(safe_cells or {start})
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return CommitmentCutAStarResult((), False, float("inf"), 0, 0, 0.0, 0.0, 0.0, 0)

    t0 = time.perf_counter()
    initial: AugmentedState = (start, frozenset())
    frontier: list[tuple[float, int, AugmentedState]] = [(0.0, 0, initial)]
    costs: dict[AugmentedState, float] = {initial: 0.0}
    parents: dict[AugmentedState, AugmentedState] = {}
    counter = 0
    expanded = 0
    cache: dict[AugmentedState, float] = {}

    def estimate(state: AugmentedState) -> float:
        if state not in cache:
            cell, active = state
            hazard = _active_hazard(model, active, cell)
            cache[state] = critical_return_cut_upper_bound(
                grid, cell, safe, hazard
            ).probability_upper_bound
        return cache[state]

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, active = state
        expanded += 1
        if cell == goal:
            states = _reconstruct(parents, state)
            profile = [estimate(item) for item in states]
            path = tuple(item[0] for item in states)
            return CommitmentCutAStarResult(
                path=path,
                success=True,
                cost=costs[state],
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=expanded,
                planning_time_ms=(time.perf_counter() - t0) * 1000.0,
                final_return_upper_bound=profile[-1],
                minimum_return_upper_bound=min(profile),
                activated_closure_count=len(active),
            )

        for neighbor in grid.neighbors4(cell):
            active2 = _next_active(model, cell, neighbor, active)
            state2: AugmentedState = (neighbor, active2)
            probability = estimate(state2)
            transition = cfg.step_cost + cfg.recoverability_weight * (1.0 - probability)
            new_cost = costs[state] + transition
            if new_cost < costs.get(state2, float("inf")):
                costs[state2] = new_cost
                parents[state2] = state
                counter += 1
                priority = new_cost + cfg.heuristic_weight * cfg.step_cost * manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, counter, state2))

    return CommitmentCutAStarResult(
        (), False, float("inf"), 0, expanded,
        (time.perf_counter() - t0) * 1000.0, 0.0, 0.0, 0
    )
