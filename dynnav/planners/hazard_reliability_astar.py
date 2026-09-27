"""A* baselines that penalize loss of safe-return reliability under future closures."""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass
from enum import Enum

from dynnav.planners.astar import AStarResult, _reconstruct_path
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.recoverability_belief import (
    TopologyHazardBelief,
    exact_safe_return_probability,
)
from dynnav.recoverability_estimation import (
    most_reliable_return_path,
    two_hazard_disjoint_return_paths,
)


class HazardReliabilityMode(str, Enum):
    SHORTEST = "shortest"
    SINGLE_RETURN = "single_return"
    REDUNDANT_RETURN = "redundant_return"
    EXACT_RETURN = "exact_return"


@dataclass(frozen=True)
class HazardReliabilityAStarConfig:
    step_cost: float = 1.0
    reliability_weight: float = 4.0
    heuristic_weight: float = 1.0
    max_hazard_cells: int = 16

    def validate(self) -> None:
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.reliability_weight < 0.0:
            raise ValueError("reliability_weight must be non-negative")
        if self.heuristic_weight < 0.0:
            raise ValueError("heuristic_weight must be non-negative")
        if self.max_hazard_cells < 0:
            raise ValueError("max_hazard_cells must be non-negative")


@dataclass(frozen=True)
class HazardReliabilityAStarResult(AStarResult):
    mode: HazardReliabilityMode
    geometric_length: int
    minimum_estimated_return_probability: float
    cumulative_return_fragility: float


def _condition_current_usable(
    hazard: TopologyHazardBelief,
    current: GridCell,
) -> TopologyHazardBelief:
    return TopologyHazardBelief(
        {
            cell: probability
            for cell, probability in hazard.closure_probability.items()
            if cell != current
        }
    )


def _return_probability(
    mode: HazardReliabilityMode,
    grid: GridMap,
    cell: GridCell,
    safe_cells: set[GridCell],
    hazard: TopologyHazardBelief,
    max_hazard_cells: int,
) -> float:
    if mode is HazardReliabilityMode.SHORTEST:
        return 1.0
    conditioned_hazard = _condition_current_usable(hazard, cell)
    if mode is HazardReliabilityMode.SINGLE_RETURN:
        return most_reliable_return_path(
            grid, cell, safe_cells, conditioned_hazard
        ).probability
    if mode is HazardReliabilityMode.EXACT_RETURN:
        return exact_safe_return_probability(
            grid,
            cell,
            safe_cells,
            conditioned_hazard,
            max_hazard_cells=max_hazard_cells,
        )
    return two_hazard_disjoint_return_paths(
        grid, cell, safe_cells, conditioned_hazard
    ).probability


def hazard_reliability_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard: TopologyHazardBelief | None = None,
    mode: HazardReliabilityMode = HazardReliabilityMode.REDUNDANT_RETURN,
    config: HazardReliabilityAStarConfig | None = None,
) -> HazardReliabilityAStarResult:
    """Plan using geometric cost plus an auditable safe-return fragility penalty.

    For each candidate state, the planner estimates the probability that at least
    one return route to the safe set survives the future closure model. The
    candidate cell is conditioned usable at the decision instant while all other
    future closure hazards remain pending. The transition penalty is
    ``reliability_weight * (1 - return_probability)``.

    This is deliberately a transparent baseline objective. It is not presented
    as a novel formulation. EXACT_RETURN uses the same exact connectivity
    oracle as the history-conditioned planner but applies it to one fixed
    state-only hazard field; this is the publication-facing representation
    ablation because it removes history without changing the return estimator.
    """

    grid.validate()
    cfg = config or HazardReliabilityAStarConfig()
    cfg.validate()
    safe = set(safe_cells or {start})
    topology_hazard = hazard or TopologyHazardBelief({})
    topology_hazard.validate(grid)

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return HazardReliabilityAStarResult(
            path=[],
            success=False,
            cost=float("inf"),
            nodes_expanded=0,
            planning_time_ms=0.0,
            mode=mode,
            geometric_length=0,
            minimum_estimated_return_probability=0.0,
            cumulative_return_fragility=float("inf"),
        )

    t0 = time.perf_counter()
    reliability_cache: dict[GridCell, float] = {}

    def reliability(cell: GridCell) -> float:
        if cell not in reliability_cache:
            reliability_cache[cell] = _return_probability(
                mode, grid, cell, safe, topology_hazard, cfg.max_hazard_cells
            )
        return reliability_cache[cell]

    frontier: list[tuple[float, int, GridCell]] = [(0.0, 0, start)]
    came_from: dict[GridCell, GridCell] = {}
    cost_so_far: dict[GridCell, float] = {start: 0.0}
    counter = 0
    nodes_expanded = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        nodes_expanded += 1
        if current == goal:
            path = _reconstruct_path(came_from, current)
            path_reliability = [reliability(cell) for cell in path]
            return HazardReliabilityAStarResult(
                path=path,
                success=True,
                cost=cost_so_far[current],
                nodes_expanded=nodes_expanded,
                planning_time_ms=(time.perf_counter() - t0) * 1000.0,
                mode=mode,
                geometric_length=max(0, len(path) - 1),
                minimum_estimated_return_probability=min(path_reliability, default=0.0),
                cumulative_return_fragility=sum(1.0 - value for value in path_reliability[1:]),
            )

        for neighbor in grid.neighbors4(current):
            return_probability = reliability(neighbor)
            transition = cfg.step_cost
            if mode is not HazardReliabilityMode.SHORTEST:
                transition += cfg.reliability_weight * (1.0 - return_probability)
            new_cost = cost_so_far[current] + transition
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                counter += 1
                priority = new_cost + cfg.heuristic_weight * cfg.step_cost * manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, counter, neighbor))

    return HazardReliabilityAStarResult(
        path=[],
        success=False,
        cost=float("inf"),
        nodes_expanded=nodes_expanded,
        planning_time_ms=(time.perf_counter() - t0) * 1000.0,
        mode=mode,
        geometric_length=0,
        minimum_estimated_return_probability=0.0,
        cumulative_return_fragility=float("inf"),
    )
