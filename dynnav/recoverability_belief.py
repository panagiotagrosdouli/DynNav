"""Exact safe-return oracle under independent topology uncertainty.

This module is intentionally evaluation-only. It enumerates all realizations of
a small set of uncertain cells and computes the exact probability that a robot
state remains connected to at least one designated safe cell. The oracle is
useful for generating ground-truth labels and validating cheaper online
estimators; it must not be fed hidden realized occupancy into a planner.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import product

from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class TopologyBelief:
    """Independent Bernoulli occupancy belief for currently unresolved cells."""

    blocked_probability: Mapping[GridCell, float]

    def validate(self, grid: GridMap) -> None:
        for cell, probability in self.blocked_probability.items():
            if not grid.in_bounds(cell):
                raise ValueError(f"uncertain cell outside grid: {cell}")
            if cell in grid.obstacles:
                raise ValueError(f"uncertain cell is already a known obstacle: {cell}")
            if not 0.0 <= probability <= 1.0:
                raise ValueError(
                    f"blocked probability must be in [0, 1], got {probability!r} for {cell}"
                )


def _can_reach_safe_region(grid: GridMap, start: GridCell, safe_cells: set[GridCell]) -> bool:
    if not grid.in_bounds(start) or not grid.passable(start):
        return False
    valid_safe = {cell for cell in safe_cells if grid.in_bounds(cell) and grid.passable(cell)}
    if not valid_safe:
        return False
    queue: deque[GridCell] = deque([start])
    reached = {start}
    while queue:
        current = queue.popleft()
        if current in valid_safe:
            return True
        for neighbor in grid.neighbors4(current):
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return False


def exact_safe_return_probability(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    belief: TopologyBelief,
    *,
    max_uncertain_cells: int = 16,
) -> float:
    """Return exact safe-return probability by enumerating topology realizations.

    The uncertain cells are assumed independent Bernoulli variables. This is an
    exact oracle for small synthetic problems, not a scalable online planner.
    The robot's current cell is conditioned free because the robot physically
    occupies it; unresolved occupancy on ``start`` would be information leakage
    in the wrong direction rather than a meaningful uncertainty model.
    """

    grid.validate()
    belief.validate(grid)
    if start in belief.blocked_probability:
        raise ValueError("start cell is physically occupied by the robot and must be conditioned free")
    if max_uncertain_cells < 0:
        raise ValueError("max_uncertain_cells must be non-negative")

    uncertain = sorted(belief.blocked_probability)
    if len(uncertain) > max_uncertain_cells:
        raise ValueError(
            f"exact enumeration limited to {max_uncertain_cells} uncertain cells; "
            f"got {len(uncertain)}"
        )

    if not uncertain:
        return float(_can_reach_safe_region(grid, start, safe_cells))

    probability_of_return = 0.0
    for blocked_flags in product((False, True), repeat=len(uncertain)):
        realization_probability = 1.0
        realized_obstacles = set(grid.obstacles)
        for cell, blocked in zip(uncertain, blocked_flags, strict=True):
            p_blocked = float(belief.blocked_probability[cell])
            realization_probability *= p_blocked if blocked else 1.0 - p_blocked
            if blocked:
                realized_obstacles.add(cell)

        if realization_probability == 0.0:
            continue
        realized_grid = GridMap.from_obstacles(
            width=grid.width,
            height=grid.height,
            obstacles=realized_obstacles,
            risk=grid.risk,
            uncertainty=grid.uncertainty,
        )
        if _can_reach_safe_region(realized_grid, start, safe_cells):
            probability_of_return += realization_probability

    return min(1.0, max(0.0, probability_of_return))


def exact_recoverability_degradation(
    grid: GridMap,
    current: GridCell,
    candidate: GridCell,
    safe_cells: set[GridCell],
    belief: TopologyBelief,
    *,
    max_uncertain_cells: int = 16,
) -> float:
    """Return loss in safe-return probability between two conditioned-free states.

    Positive values mean the candidate state preserves less safe-return
    probability than the current state under the same unresolved topology
    belief. This quantity is useful diagnostically, but by itself it is not a
    novel one-step objective: with fixed current state it induces the same action
    ordering as maximizing candidate safe-return probability.
    """

    current_probability = exact_safe_return_probability(
        grid,
        current,
        safe_cells,
        belief,
        max_uncertain_cells=max_uncertain_cells,
    )
    candidate_probability = exact_safe_return_probability(
        grid,
        candidate,
        safe_cells,
        belief,
        max_uncertain_cells=max_uncertain_cells,
    )
    return current_probability - candidate_probability
