"""Exact augmented-state A* over quotient closure-event history.

This planner is the G5 counterpart to commitment_aware_astar. It replaces
activated trigger identities with the exact closure-event quotient from
history_compression. Under the independent-closure semantics, duplicate
triggers that activate the same (closure cell, probability) event do not create
distinct planning states.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.history_compression import (
    HazardEventQuotient,
    build_hazard_event_quotient,
    quotient_return_probability,
)
from dynnav.planners.grid_map import GridCell, GridMap, manhattan

CompressedState = tuple[GridCell, frozenset[int]]


@dataclass(frozen=True)
class CompressedCommitmentAStarConfig:
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
class CompressedCommitmentAStarResult:
    path: tuple[GridCell, ...]
    success: bool
    cost: float
    geometric_length: int
    nodes_expanded: int
    planning_time_ms: float
    final_return_probability: float
    minimum_return_probability: float
    activated_event_count: int
    raw_hazard_count: int
    quotient_event_count: int


def _events_after_transition(
    model: CommitmentHazardModel,
    quotient: HazardEventQuotient,
    current: GridCell,
    neighbor: GridCell,
    active_events: frozenset[int],
) -> frozenset[int]:
    additions = {
        quotient.event_by_hazard_index[index]
        for index, closure in enumerate(model.closures)
        if closure.trigger == (current, neighbor)
    }
    return active_events | frozenset(additions)


def _return_probability(
    grid: GridMap,
    cell: GridCell,
    safe_cells: set[GridCell],
    quotient: HazardEventQuotient,
    active_events: frozenset[int],
    max_hazard_cells: int,
) -> float:
    return quotient_return_probability(
        grid,
        cell,
        safe_cells,
        quotient,
        active_events,
        max_hazard_cells=max_hazard_cells,
    )


def compressed_commitment_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    config: CompressedCommitmentAStarConfig | None = None,
    initial_activated_closures: frozenset[int] | None = None,
) -> CompressedCommitmentAStarResult:
    """Plan exactly while quotienting duplicate future closure events."""

    grid.validate()
    cfg = config or CompressedCommitmentAStarConfig()
    cfg.validate()
    safe = set(safe_cells) if safe_cells is not None else {start}
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)
    quotient = build_hazard_event_quotient(model)

    initial_raw = frozenset(initial_activated_closures or ())
    initial_events = quotient.compress_active_indices(initial_raw)

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return CompressedCommitmentAStarResult(
            (),
            False,
            float("inf"),
            0,
            0,
            0.0,
            0.0,
            0.0,
            len(initial_events),
            quotient.hazard_count,
            quotient.event_count,
        )

    initial: CompressedState = (start, initial_events)
    frontier: list[tuple[float, int, CompressedState]] = [(0.0, 0, initial)]
    costs: dict[CompressedState, float] = {initial: 0.0}
    parents: dict[CompressedState, CompressedState] = {}
    counter = 0
    nodes_expanded = 0
    t0 = time.perf_counter()

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, active_events = state
        nodes_expanded += 1

        if cell == goal:
            planning_time_ms = (time.perf_counter() - t0) * 1000.0
            states = [state]
            cursor = state
            while cursor in parents:
                cursor = parents[cursor]
                states.append(cursor)
            states.reverse()
            path = tuple(item[0] for item in states)
            probabilities = [
                _return_probability(
                    grid,
                    item_cell,
                    safe,
                    quotient,
                    item_events,
                    cfg.max_hazard_cells,
                )
                for item_cell, item_events in states
            ]
            return CompressedCommitmentAStarResult(
                path=path,
                success=True,
                cost=costs[state],
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=nodes_expanded,
                planning_time_ms=planning_time_ms,
                final_return_probability=probabilities[-1],
                minimum_return_probability=min(probabilities),
                activated_event_count=len(states[-1][1]),
                raw_hazard_count=quotient.hazard_count,
                quotient_event_count=quotient.event_count,
            )

        for neighbor in grid.neighbors4(cell):
            next_events = _events_after_transition(
                model,
                quotient,
                cell,
                neighbor,
                active_events,
            )
            next_state: CompressedState = (neighbor, next_events)
            probability = _return_probability(
                grid,
                neighbor,
                safe,
                quotient,
                next_events,
                cfg.max_hazard_cells,
            )
            transition = cfg.step_cost + cfg.recoverability_weight * (1.0 - probability)
            new_cost = costs[state] + transition
            if new_cost < costs.get(next_state, float("inf")):
                costs[next_state] = new_cost
                parents[next_state] = state
                counter += 1
                priority = new_cost + cfg.heuristic_weight * cfg.step_cost * manhattan(
                    neighbor,
                    goal,
                )
                heapq.heappush(frontier, (priority, counter, next_state))

    return CompressedCommitmentAStarResult(
        (),
        False,
        float("inf"),
        0,
        nodes_expanded,
        (time.perf_counter() - t0) * 1000.0,
        0.0,
        0.0,
        len(initial_events),
        quotient.hazard_count,
        quotient.event_count,
    )
