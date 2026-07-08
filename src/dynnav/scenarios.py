"""Synthetic scenario generation for reproducible DynNav benchmarks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dynnav.core import GridMap, Pose


@dataclass(frozen=True, slots=True)
class Scenario:
    """A deterministic planning scenario."""

    grid: GridMap
    start: Pose
    goal: Pose
    seed: int


def generate_scenario(
    width: int,
    height: int,
    obstacle_density: float,
    unknown_fraction: float,
    seed: int,
) -> Scenario:
    """Generate a seeded grid-world scenario with soft uncertainty."""
    rng = np.random.default_rng(seed)
    occupancy = rng.random((height, width))
    occupancy = (occupancy < obstacle_density).astype(float)
    unknown = rng.random((height, width)) < unknown_fraction
    occupancy[unknown] = rng.uniform(0.25, 0.75, size=int(unknown.sum()))
    start = Pose(1, 1)
    goal = Pose(width - 2, height - 2)
    occupancy[start.y, start.x] = 0.0
    occupancy[goal.y, goal.x] = 0.0
    return Scenario(GridMap(occupancy), start, goal, seed)
