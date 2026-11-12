"""Auditable small-world example of position/history aliasing.

This is a deterministic synthetic mathematical demonstration, not a robot trial.
"""
from __future__ import annotations

from dataclasses import dataclass

from dynnav.commitment_hazard import (
    CommitmentClosure, CommitmentHazardModel,
    exact_history_conditioned_return_probability,
)
from dynnav.planners.grid_map import GridMap, GridCell

SAFE: GridCell = (0, 2)
ENDPOINT: GridCell = (4, 2)
TRIGGER = ((3, 1), (4, 1))
CLOSURE: GridCell = (2, 2)
FREE: frozenset[GridCell] = frozenset({
    (0, 2), (1, 2), (2, 2), (3, 2), (4, 2),
    (3, 1), (4, 1), (3, 3), (4, 3),
})
SAFE_HISTORY = ((0, 2), (1, 2), (2, 2), (3, 2), (4, 2))
RISKY_HISTORY = (
    (0, 2), (1, 2), (2, 2), (3, 2),
    (3, 1), (4, 1), (4, 2),
)


@dataclass(frozen=True)
class HistoryComparison:
    probability: float
    safe_return_probability: float
    risky_return_probability: float
    separation: float
    endpoint_only_minimax_error_bound: float


def small_world() -> GridMap:
    occupied = frozenset(
        (x, y) for x in range(5) for y in range(5) if (x, y) not in FREE
    )
    return GridMap.from_obstacles(5, 5, occupied)


def compare_histories(probability: float) -> HistoryComparison:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("closure probability must be in [0, 1]")
    grid = small_world()
    model = CommitmentHazardModel((CommitmentClosure(
        trigger=TRIGGER,
        closure_cell=CLOSURE,
        closure_probability=float(probability),
    ),))
    safe = exact_history_conditioned_return_probability(
        grid, SAFE_HISTORY, {SAFE}, model
    )
    risky = exact_history_conditioned_return_probability(
        grid, RISKY_HISTORY, {SAFE}, model
    )
    separation = abs(safe - risky)
    return HistoryComparison(
        probability=float(probability),
        safe_return_probability=safe,
        risky_return_probability=risky,
        separation=separation,
        endpoint_only_minimax_error_bound=separation / 2.0,
    )
