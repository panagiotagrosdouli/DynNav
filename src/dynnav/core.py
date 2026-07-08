"""Core navigation data structures used across DynNav modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True, slots=True)
class Pose:
    """Discrete grid pose."""

    x: int
    y: int


@dataclass(frozen=True, slots=True)
class Trajectory:
    """A planned route with scalar diagnostics."""

    poses: tuple[Pose, ...]
    cost: float
    risk: float
    recoverability: float

    @property
    def length(self) -> int:
        """Return the number of poses in the trajectory."""
        return len(self.poses)


@dataclass(slots=True)
class GridMap:
    """Occupancy belief grid.

    Values are interpreted as obstacle probabilities in [0, 1]. A value close to
    1 is likely occupied; a value close to 0 is likely free.
    """

    occupancy: np.ndarray
    resolution: float = 1.0

    def __post_init__(self) -> None:
        if self.occupancy.ndim != 2:
            raise ValueError("occupancy must be a 2-D array")
        self.occupancy = np.clip(self.occupancy.astype(float), 0.0, 1.0)

    @property
    def shape(self) -> tuple[int, int]:
        """Return grid shape as (height, width)."""
        return self.occupancy.shape

    def in_bounds(self, pose: Pose) -> bool:
        """Return whether a pose lies inside the grid."""
        height, width = self.shape
        return 0 <= pose.y < height and 0 <= pose.x < width

    def probability(self, pose: Pose) -> float:
        """Return obstacle probability at a pose."""
        if not self.in_bounds(pose):
            return 1.0
        return float(self.occupancy[pose.y, pose.x])

    def neighbors4(self, pose: Pose) -> Iterable[Pose]:
        """Yield four-connected neighboring poses inside the grid."""
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = Pose(pose.x + dx, pose.y + dy)
            if self.in_bounds(candidate):
                yield candidate
