"""Hard safe-return constrained A* for history-conditioned closure hazards."""
from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability

AugmentedState = tuple[GridCell, frozenset[int]]


@dataclass(frozen=True)
class SafeReturnConstraintConfig:
    minimum_return_probability: float = 0.9
    step_cost: float = 1.0
    heuristic_weight: float = 1.0
    max_hazard_cells: int = 16

    def validate(self) -> None:
        if not 0.0 <= self.minimum_return_probability <= 1.0:
            raise ValueError("minimum_return_probability must be in [0, 1]")
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.heuristic_weight < 0.0:
            raise ValueError("heuristic_weight must be non-negative")
        if self.max_hazard_cells < 0:
            raise ValueError("max_hazard_cells must be non-negative")


@dataclass(frozen=True)
class SafeReturnConstraintResult:
    path: tuple[GridCell, ...]
    success: bool
    geometric_length: int
    nodes_expanded: int
    planning_time_ms: float
    final_return_probability: float
    minimum_return_probability: float
    activated_closure_count: int
    rejected_transitions: int


def _next_active(
    model: CommitmentHazardModel,
    current: GridCell,
    neighbor: GridCell,
    active: frozenset[int],
) -> frozenset[int]:
    return active | frozenset(
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger == (current, neighbor)
    )


def _hazard(
    model: CommitmentHazardModel,
    active: frozenset[int],
    current: GridCell,
) -> TopologyHazardBelief:
    values: dict[GridCell, float] = {}
    for index in active:
        closure = model.closures[index]
        if closure.closure_cell == current:
            continue
        prior = values.get(closure.closure_cell)
        if prior is not None and prior != closure.closure_probability:
            raise ValueError("conflicting active closure probabilities")
        values[closure.closure_cell] = closure.closure_probability
    return TopologyHazardBelief(values)


def _reconstruct(
    parents: dict[AugmentedState, AugmentedState],
    state: AugmentedState,
) -> tuple[AugmentedState, ...]:
    states = [state]
    while state in parents:
        state = parents[state]
        states.append(state)
    states.reverse()
    return tuple(states)


def commitment_safe_return_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    config: SafeReturnConstraintConfig | None = None,
) -> SafeReturnConstraintResult:
    """Shortest path subject to a per-state history-conditioned return constraint.

    Every accepted successor must retain at least ``minimum_return_probability``
    of reaching the designated safe set under the active future-closure model.
    ``planning_time_ms`` includes the initial safe-return feasibility check and
    all online oracle calls used to accept or reject successors, but excludes
    post-goal diagnostic profile construction.
    """
    grid.validate()
    cfg = config or SafeReturnConstraintConfig()
    cfg.validate()
    safe = set(safe_cells or {start})
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return SafeReturnConstraintResult((), False, 0, 0, 0.0, 0.0, 0.0, 0, 0)

    start_state: AugmentedState = (start, frozenset())
    cache: dict[AugmentedState, float] = {}

    def return_probability(state: AugmentedState) -> float:
        if state not in cache:
            cell, active = state
            cache[state] = exact_safe_return_probability(
                grid,
                cell,
                safe,
                _hazard(model, active, cell),
                max_hazard_cells=cfg.max_hazard_cells,
            )
        return cache[state]

    t0 = time.perf_counter()
    if return_probability(start_state) < cfg.minimum_return_probability:
        return SafeReturnConstraintResult(
            (), False, 0, 0, (time.perf_counter() - t0) * 1000.0,
            0.0, 0.0, 0, 0
        )

    frontier: list[tuple[float, int, AugmentedState]] = [(0.0, 0, start_state)]
    costs: dict[AugmentedState, float] = {start_state: 0.0}
    parents: dict[AugmentedState, AugmentedState] = {}
    counter = 0
    expanded = 0
    rejected = 0

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, active = state
        expanded += 1
        if cell == goal:
            planning_time_ms = (time.perf_counter() - t0) * 1000.0
            states = _reconstruct(parents, state)
            profile = [return_probability(item) for item in states]
            path = tuple(item[0] for item in states)
            return SafeReturnConstraintResult(
                path=path,
                success=True,
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=expanded,
                planning_time_ms=planning_time_ms,
                final_return_probability=profile[-1],
                minimum_return_probability=min(profile),
                activated_closure_count=len(active),
                rejected_transitions=rejected,
            )

        for neighbor in grid.neighbors4(cell):
            next_state: AugmentedState = (
                neighbor,
                _next_active(model, cell, neighbor, active),
            )
            if return_probability(next_state) < cfg.minimum_return_probability:
                rejected += 1
                continue
            new_cost = costs[state] + cfg.step_cost
            if new_cost < costs.get(next_state, float("inf")):
                costs[next_state] = new_cost
                parents[next_state] = state
                counter += 1
                priority = new_cost + cfg.heuristic_weight * cfg.step_cost * manhattan(
                    neighbor, goal
                )
                heapq.heappush(frontier, (priority, counter, next_state))

    return SafeReturnConstraintResult(
        (), False, 0, expanded, (time.perf_counter() - t0) * 1000.0,
        0.0, 0.0, 0, rejected
    )
