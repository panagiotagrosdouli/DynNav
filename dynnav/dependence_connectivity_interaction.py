"""Two-hazard connectivity interaction under fixed closure marginals.

For two binary closure events C1 and C2 with fixed marginals p1 and p2, every
admissible joint law is determined by q = P(C1=1, C2=1). For any deterministic
return-connectivity indicator f(c1, c2), expected return reliability is affine
in q. The slope is the discrete interaction

    kappa = f00 - f10 - f01 + f11.

Thus the sign of dependence sensitivity is a graph/topology property:

* kappa < 0: stronger positive dependence lowers return reliability;
* kappa = 0: dependence does not matter at fixed marginals;
* kappa > 0: stronger positive dependence raises return reliability.

The result is exact for the two-hazard bounded model and does not rely on a
specific grid geometry.
"""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import _can_reach_safe_region


@dataclass(frozen=True)
class ConnectivityTruthTable:
    neither_closed: int
    first_closed: int
    second_closed: int
    both_closed: int

    def validate(self) -> None:
        values = (
            self.neither_closed,
            self.first_closed,
            self.second_closed,
            self.both_closed,
        )
        if any(value not in (0, 1) for value in values):
            raise ValueError("connectivity truth-table values must be binary")

    @property
    def interaction(self) -> int:
        """Discrete second difference controlling dependence sensitivity."""

        self.validate()
        return (
            self.neither_closed
            - self.first_closed
            - self.second_closed
            + self.both_closed
        )


def connectivity_truth_table(
    grid: GridMap,
    start: GridCell,
    safe_cells: set[GridCell],
    first_hazard: GridCell,
    second_hazard: GridCell,
) -> ConnectivityTruthTable:
    """Evaluate return connectivity under all four two-hazard realizations."""

    grid.validate()
    if first_hazard == second_hazard:
        raise ValueError("hazards must be distinct")
    for hazard in (first_hazard, second_hazard):
        if not grid.in_bounds(hazard) or not grid.passable(hazard):
            raise ValueError(f"hazard must be a free in-bounds cell: {hazard}")

    def connected(closed: frozenset[GridCell]) -> int:
        obstacles = set(grid.obstacles)
        obstacles.update(cell for cell in closed if cell != start)
        realized = GridMap.from_obstacles(
            grid.width,
            grid.height,
            obstacles=obstacles,
            risk=grid.risk,
            uncertainty=grid.uncertainty,
        )
        return int(_can_reach_safe_region(realized, start, safe_cells))

    return ConnectivityTruthTable(
        neither_closed=connected(frozenset()),
        first_closed=connected(frozenset({first_hazard})),
        second_closed=connected(frozenset({second_hazard})),
        both_closed=connected(frozenset({first_hazard, second_hazard})),
    )


def expected_return_from_joint(
    table: ConnectivityTruthTable,
    *,
    p_first: float,
    p_second: float,
    joint_closure: float,
) -> float:
    """Evaluate return reliability from marginals plus q=P(C1=1,C2=1)."""

    table.validate()
    if not 0.0 <= p_first <= 1.0 or not 0.0 <= p_second <= 1.0:
        raise ValueError("marginal closure probabilities must be in [0, 1]")
    lower = max(0.0, p_first + p_second - 1.0)
    upper = min(p_first, p_second)
    if not lower <= joint_closure <= upper:
        raise ValueError(
            f"joint_closure must satisfy Frechet bounds [{lower}, {upper}]"
        )

    p00 = 1.0 - p_first - p_second + joint_closure
    p10 = p_first - joint_closure
    p01 = p_second - joint_closure
    p11 = joint_closure
    return (
        table.neither_closed * p00
        + table.first_closed * p10
        + table.second_closed * p01
        + table.both_closed * p11
    )


def dependence_sensitivity(table: ConnectivityTruthTable) -> int:
    """Return d R / d q for fixed closure marginals."""

    return table.interaction
