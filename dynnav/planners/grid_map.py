"""Grid map representation for DynNav planners."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

GridCell = tuple[int, int]


@dataclass(frozen=True)
class GridMap:
    """Small dependency-free grid map with risk and uncertainty layers.

    Args:
        width: Number of columns.
        height: Number of rows.
        obstacles: Occupied cells that cannot be traversed.
        risk: Optional normalized risk per cell in [0, 1].
        uncertainty: Optional normalized map uncertainty per cell in [0, 1].
    """

    width: int
    height: int
    obstacles: frozenset[GridCell] = field(default_factory=frozenset)
    risk: dict[GridCell, float] = field(default_factory=dict)
    uncertainty: dict[GridCell, float] = field(default_factory=dict)

    @classmethod
    def from_obstacles(
        cls,
        width: int,
        height: int,
        obstacles: Iterable[GridCell] = (),
        risk: dict[GridCell, float] | None = None,
        uncertainty: dict[GridCell, float] | None = None,
    ) -> "GridMap":
        grid = cls(
            width=width,
            height=height,
            obstacles=frozenset(obstacles),
            risk=dict(risk or {}),
            uncertainty=dict(uncertainty or {}),
        )
        grid.validate()
        return grid

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        for cell in self.obstacles:
            if not self.in_bounds(cell):
                raise ValueError(f"obstacle outside grid: {cell}")
        for layer_name, layer in (("risk", self.risk), ("uncertainty", self.uncertainty)):
            for cell, value in layer.items():
                if not self.in_bounds(cell):
                    raise ValueError(f"{layer_name} cell outside grid: {cell}")
                if not 0.0 <= value <= 1.0:
                    raise ValueError(f"{layer_name} value must be in [0, 1], got {value!r}")

    def in_bounds(self, cell: GridCell) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, cell: GridCell) -> bool:
        return cell not in self.obstacles

    def neighbors4(self, cell: GridCell) -> list[GridCell]:
        x, y = cell
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [c for c in candidates if self.in_bounds(c) and self.passable(c)]

    def cell_risk(self, cell: GridCell) -> float:
        return self.risk.get(cell, 0.0)

    def cell_uncertainty(self, cell: GridCell) -> float:
        return self.uncertainty.get(cell, 0.0)

    def occupancy_belief(self) -> dict[GridCell, float]:
        """Return occupancy probabilities for information-gain scoring.

        Obstacles are certain occupied cells. Free cells use uncertainty as a
        proxy for occupancy ambiguity, centered around 0.5 when uncertainty is
        high.
        """
        belief: dict[GridCell, float] = {}
        for x in range(self.width):
            for y in range(self.height):
                cell = (x, y)
                if cell in self.obstacles:
                    belief[cell] = 1.0
                else:
                    uncertainty = self.cell_uncertainty(cell)
                    belief[cell] = 0.1 + 0.4 * uncertainty
        return belief


def manhattan(a: GridCell, b: GridCell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
