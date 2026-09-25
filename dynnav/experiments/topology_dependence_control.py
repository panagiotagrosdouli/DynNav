"""Exploratory G1 topology/dependence sign-reversal control.

The same two closure marginals can interact with dependence in opposite ways
depending on graph structure. This post-full-study diagnostic prevents a
misleading claim that positive dependence is uniformly harmful.
"""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_scenarios import (
    ClosureScenario,
    TopologyScenarioBelief,
    exact_scenario_safe_return_probability,
)


@dataclass(frozen=True)
class TopologyDependenceRecord:
    topology: str
    dependence: str
    return_probability: float


def _parallel_return_problem() -> tuple[GridMap, GridCell, set[GridCell], tuple[GridCell, GridCell]]:
    free = {
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 2),
        (1, 2),
        (2, 2),
        (0, 1),
        (2, 1),
    }
    obstacles = {
        (x, y)
        for x in range(3)
        for y in range(3)
        if (x, y) not in free
    }
    return (
        GridMap.from_obstacles(3, 3, obstacles=obstacles),
        (2, 1),
        {(0, 1)},
        ((1, 0), (1, 2)),
    )


def _serial_return_problem() -> tuple[GridMap, GridCell, set[GridCell], tuple[GridCell, GridCell]]:
    grid = GridMap.from_obstacles(4, 1)
    return grid, (3, 0), {(0, 0)}, ((1, 0), (2, 0))


def _belief(
    first: GridCell,
    second: GridCell,
    dependence: str,
) -> TopologyScenarioBelief:
    if dependence == "independent":
        return TopologyScenarioBelief(
            (
                ClosureScenario(frozenset(), 0.25),
                ClosureScenario(frozenset({first}), 0.25),
                ClosureScenario(frozenset({second}), 0.25),
                ClosureScenario(frozenset({first, second}), 0.25),
            )
        )
    if dependence == "common_cause":
        return TopologyScenarioBelief(
            (
                ClosureScenario(frozenset(), 0.5),
                ClosureScenario(frozenset({first, second}), 0.5),
            )
        )
    if dependence == "anti_correlated":
        return TopologyScenarioBelief(
            (
                ClosureScenario(frozenset({first}), 0.5),
                ClosureScenario(frozenset({second}), 0.5),
            )
        )
    raise ValueError(f"unknown dependence: {dependence}")


def run_topology_dependence_control() -> list[TopologyDependenceRecord]:
    """Evaluate equal marginals across parallel and serial return structures."""

    records: list[TopologyDependenceRecord] = []
    for topology, builder in (
        ("parallel_redundant", _parallel_return_problem),
        ("serial_cut", _serial_return_problem),
    ):
        grid, current, safe, hazards = builder()
        for dependence in ("independent", "common_cause", "anti_correlated"):
            probability = exact_scenario_safe_return_probability(
                grid,
                current,
                safe,
                _belief(hazards[0], hazards[1], dependence),
            )
            records.append(
                TopologyDependenceRecord(
                    topology=topology,
                    dependence=dependence,
                    return_probability=probability,
                )
            )
    return records
