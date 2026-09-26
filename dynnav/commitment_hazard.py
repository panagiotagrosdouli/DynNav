"""History-conditioned route-closure hazards for commitment analysis.

This module represents hazards that become active only after a directed
transition is taken. It is deliberately small and deterministic so we can test
whether a state-only recoverability model loses information about how the robot
arrived at the same geometric state.
"""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import (
    TopologyHazardBelief,
    exact_safe_return_probability,
)

DirectedTransition = tuple[GridCell, GridCell]


@dataclass(frozen=True)
class CommitmentClosure:
    """A closure event activated by traversing one directed transition."""

    trigger: DirectedTransition
    closure_cell: GridCell
    closure_probability: float

    def validate(self, grid: GridMap) -> None:
        source, target = self.trigger
        if target not in grid.neighbors4(source):
            raise ValueError(f"trigger is not a traversable grid edge: {self.trigger}")
        if not grid.in_bounds(self.closure_cell) or not grid.passable(self.closure_cell):
            raise ValueError(f"closure cell must be currently free: {self.closure_cell}")
        if not 0.0 <= self.closure_probability <= 1.0:
            raise ValueError("closure_probability must be in [0, 1]")


@dataclass(frozen=True)
class CommitmentHazardModel:
    closures: tuple[CommitmentClosure, ...]

    def validate(self, grid: GridMap) -> None:
        seen: set[DirectedTransition] = set()
        cell_probabilities: dict[GridCell, float] = {}
        for closure in self.closures:
            closure.validate(grid)
            if closure.trigger in seen:
                raise ValueError(f"duplicate trigger: {closure.trigger}")
            seen.add(closure.trigger)
            existing = cell_probabilities.get(closure.closure_cell)
            if existing is not None and existing != closure.closure_probability:
                raise ValueError(
                    "triggers mapped to the same closure cell must use one "
                    f"probability: {closure.closure_cell}"
                )
            cell_probabilities[closure.closure_cell] = closure.closure_probability

    def activated_hazard_for_path(
        self,
        grid: GridMap,
        path: tuple[GridCell, ...] | list[GridCell],
    ) -> TopologyHazardBelief:
        """Return the hazard belief activated by the transitions in ``path``."""

        self.validate(grid)
        if not path:
            raise ValueError("path cannot be empty")
        for cell in path:
            if not grid.in_bounds(cell) or not grid.passable(cell):
                raise ValueError(f"path contains invalid cell: {cell}")
        for source, target in zip(path, path[1:], strict=False):
            if target not in grid.neighbors4(source):
                raise ValueError(f"path contains non-traversable transition: {(source, target)}")

        traversed = set(zip(path, path[1:], strict=False))
        probabilities: dict[GridCell, float] = {}
        for closure in self.closures:
            if closure.trigger not in traversed:
                continue
            existing = probabilities.get(closure.closure_cell)
            if existing is not None and existing != closure.closure_probability:
                raise ValueError(
                    "multiple activated triggers assign different probabilities "
                    f"to closure cell {closure.closure_cell}"
                )
            probabilities[closure.closure_cell] = closure.closure_probability
        return TopologyHazardBelief(probabilities)


def exact_history_conditioned_return_probability(
    grid: GridMap,
    path: tuple[GridCell, ...] | list[GridCell],
    safe_cells: set[GridCell],
    model: CommitmentHazardModel,
    *,
    max_hazard_cells: int = 16,
) -> float:
    """Evaluate exact return reliability at the path endpoint after commitment.

    Unlike a state-only recoverability function, this quantity depends on the
    transitions used to reach the current state because those transitions may
    activate different future closure events.
    """

    if not path:
        raise ValueError("path cannot be empty")
    hazard = model.activated_hazard_for_path(grid, path)
    current = path[-1]
    # If a trigger activates a future closure at the robot's current cell, that
    # closure cannot have occurred before the robot occupies the cell. Condition
    # the current cell usable and retain all other activated hazards.
    conditioned = TopologyHazardBelief(
        {
            cell: probability
            for cell, probability in hazard.closure_probability.items()
            if cell != current
        }
    )
    return exact_safe_return_probability(
        grid,
        current,
        safe_cells,
        conditioned,
        max_hazard_cells=max_hazard_cells,
    )
