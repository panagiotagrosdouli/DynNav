"""Augmented-state A* using worst-case return reliability over dependence ambiguity."""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.distributional_recoverability import (
    PairwiseClosureConstraint,
    ProbabilityInterval,
    TopologyAmbiguitySet,
    robust_safe_return_probability,
)
from dynnav.planners.grid_map import GridCell, GridMap, manhattan

AugmentedState = tuple[GridCell, frozenset[int]]


@dataclass(frozen=True)
class RobustCommitmentAStarConfig:
    step_cost: float = 1.0
    recoverability_weight: float = 4.0
    heuristic_weight: float = 1.0
    max_hazard_cells: int = 12
    pairwise_constraints: tuple[PairwiseClosureConstraint, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")
        if self.heuristic_weight < 0.0:
            raise ValueError("heuristic_weight must be non-negative")
        if self.max_hazard_cells < 0:
            raise ValueError("max_hazard_cells must be non-negative")
        for constraint in self.pairwise_constraints:
            constraint.validate()


@dataclass(frozen=True)
class RobustCommitmentAStarResult:
    path: tuple[GridCell, ...]
    success: bool
    cost: float
    geometric_length: int
    nodes_expanded: int
    planning_time_ms: float
    final_worst_case_return_probability: float
    minimum_worst_case_return_probability: float
    activated_hazard_count: int


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


def _ambiguity_from_active(
    model: CommitmentHazardModel,
    active: frozenset[int],
    current: GridCell,
    pairwise_constraints: tuple[PairwiseClosureConstraint, ...],
) -> TopologyAmbiguitySet:
    marginals: dict[GridCell, ProbabilityInterval] = {}
    for index in active:
        closure = model.closures[index]
        if closure.closure_cell == current:
            continue
        interval = ProbabilityInterval(
            float(closure.closure_probability),
            float(closure.closure_probability),
        )
        existing = marginals.get(closure.closure_cell)
        if existing is not None and existing != interval:
            raise ValueError(
                "active hazards assign conflicting marginal probabilities "
                f"to {closure.closure_cell}"
            )
        marginals[closure.closure_cell] = interval
    active_cells = set(marginals)
    relevant_pairwise = tuple(
        constraint
        for constraint in pairwise_constraints
        if constraint.first in active_cells and constraint.second in active_cells
    )
    return TopologyAmbiguitySet(marginals=marginals, pairwise=relevant_pairwise)


def _return_probability(
    grid: GridMap,
    cell: GridCell,
    safe_cells: set[GridCell],
    model: CommitmentHazardModel,
    active: frozenset[int],
    config: RobustCommitmentAStarConfig,
) -> float:
    ambiguity = _ambiguity_from_active(
        model,
        active,
        cell,
        config.pairwise_constraints,
    )
    return robust_safe_return_probability(
        grid,
        cell,
        safe_cells,
        ambiguity,
        max_hazard_cells=config.max_hazard_cells,
    )


def robust_commitment_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    config: RobustCommitmentAStarConfig | None = None,
    initial_activated_closures: frozenset[int] | None = None,
) -> RobustCommitmentAStarResult:
    """Plan with the lower safe-return probability over allowed dependence."""

    grid.validate()
    cfg = config or RobustCommitmentAStarConfig()
    cfg.validate()
    safe = set(safe_cells) if safe_cells is not None else {start}
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)
    initial_active = frozenset(initial_activated_closures or ())
    invalid = sorted(index for index in initial_active if index < 0 or index >= len(model.closures))
    if invalid:
        raise ValueError(f"initial activated hazard indices are out of range: {invalid}")
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return RobustCommitmentAStarResult(
            (), False, float("inf"), 0, 0, 0.0, 0.0, 0.0, len(initial_active)
        )

    initial: AugmentedState = (start, initial_active)
    frontier: list[tuple[float, int, AugmentedState]] = [(0.0, 0, initial)]
    costs: dict[AugmentedState, float] = {initial: 0.0}
    parents: dict[AugmentedState, AugmentedState] = {}
    counter = 0
    nodes_expanded = 0
    t0 = time.perf_counter()

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, active = state
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
                _return_probability(grid, c, safe, model, a, cfg)
                for c, a in states
            ]
            return RobustCommitmentAStarResult(
                path=path,
                success=True,
                cost=costs[state],
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=nodes_expanded,
                planning_time_ms=planning_time_ms,
                final_worst_case_return_probability=probabilities[-1],
                minimum_worst_case_return_probability=min(probabilities),
                activated_hazard_count=len(states[-1][1]),
            )

        for neighbor in grid.neighbors4(cell):
            next_active = _activated_after_transition(model, cell, neighbor, active)
            next_state: AugmentedState = (neighbor, next_active)
            probability = _return_probability(grid, neighbor, safe, model, next_active, cfg)
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

    return RobustCommitmentAStarResult(
        (),
        False,
        float("inf"),
        0,
        nodes_expanded,
        (time.perf_counter() - t0) * 1000.0,
        0.0,
        0.0,
        len(initial_active),
    )
