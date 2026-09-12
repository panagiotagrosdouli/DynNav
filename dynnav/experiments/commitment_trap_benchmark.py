"""Controlled commitment-trap benchmark for future route-closure recoverability."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.planners.recoverability_astar import (
    PlannerMode,
    RecoverabilityAStarConfig,
    recoverability_astar,
)
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability


@dataclass(frozen=True)
class CommitmentTrapRecord:
    closure_probability: float
    reliability_weight: float
    planner: str
    geometric_length: int
    uses_fragile_corridor: bool
    minimum_exact_return_probability: float
    mean_exact_return_probability: float
    planning_time_ms: float
    nodes_expanded: int


def commitment_trap_world(
    closure_probability: float,
) -> tuple[GridMap, GridCell, GridCell, set[GridCell], TopologyHazardBelief]:
    """Create a short fragile corridor and a long hazard-free return corridor.

    The free space is a rectangular loop. The nominal start/goal lie on the
    short top corridor. Two cells on that corridor may independently close in
    the future. A robot located between them can return to the launch safe set
    through the left gate or continue through the right gate and use the long
    lower corridor. If both gates close, that committed region loses its return
    connection. The lower corridor contains no closure hazards.
    """

    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")

    width, height = 9, 7
    free: set[GridCell] = set()
    free.update((x, 1) for x in range(width))
    free.update((x, 5) for x in range(width))
    free.update((0, y) for y in range(1, 6))
    free.update((8, y) for y in range(1, 6))
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    start = (0, 1)
    goal = (8, 1)
    safe = {start}
    hazard = TopologyHazardBelief(
        {(2, 1): closure_probability, (6, 1): closure_probability}
    )
    return grid, start, goal, safe, hazard


def _condition_current_usable(
    hazard: TopologyHazardBelief,
    current: GridCell,
) -> TopologyHazardBelief:
    """Condition the occupied robot cell usable while retaining other future hazards."""

    return TopologyHazardBelief(
        {
            cell: probability
            for cell, probability in hazard.closure_probability.items()
            if cell != current
        }
    )


def _exact_path_metrics(
    grid: GridMap,
    path: list[GridCell],
    safe: set[GridCell],
    hazard: TopologyHazardBelief,
) -> tuple[float, float]:
    values = [
        exact_safe_return_probability(
            grid,
            cell,
            safe,
            _condition_current_usable(hazard, cell),
            max_hazard_cells=2,
        )
        for cell in path
    ]
    return min(values), sum(values) / len(values)


def run_commitment_trap_benchmark(
    closure_probabilities: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9),
    reliability_weights: tuple[float, ...] = (1.0, 2.0, 4.0, 6.0, 8.0),
) -> list[CommitmentTrapRecord]:
    if not closure_probabilities or not reliability_weights:
        raise ValueError("probabilities and weights must be non-empty")

    records: list[CommitmentTrapRecord] = []
    for probability in closure_probabilities:
        grid, start, goal, safe, hazard = commitment_trap_world(probability)

        shortest = recoverability_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            mode=PlannerMode.SHORTEST,
        )
        structural = recoverability_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            mode=PlannerMode.RECOVERABILITY_AWARE,
            config=RecoverabilityAStarConfig(irreversibility_weight=4.0),
        )
        for name, result in (("shortest", shortest), ("structural", structural)):
            minimum_exact, mean_exact = _exact_path_metrics(grid, result.path, safe, hazard)
            records.append(
                CommitmentTrapRecord(
                    closure_probability=probability,
                    reliability_weight=0.0,
                    planner=name,
                    geometric_length=result.geometric_length,
                    uses_fragile_corridor=(4, 1) in result.path,
                    minimum_exact_return_probability=minimum_exact,
                    mean_exact_return_probability=mean_exact,
                    planning_time_ms=result.planning_time_ms,
                    nodes_expanded=result.nodes_expanded,
                )
            )

        for weight in reliability_weights:
            config = HazardReliabilityAStarConfig(reliability_weight=weight)
            for mode in (
                HazardReliabilityMode.SINGLE_RETURN,
                HazardReliabilityMode.REDUNDANT_RETURN,
            ):
                result = hazard_reliability_astar(
                    grid,
                    start,
                    goal,
                    safe_cells=safe,
                    hazard=hazard,
                    mode=mode,
                    config=config,
                )
                minimum_exact, mean_exact = _exact_path_metrics(grid, result.path, safe, hazard)
                records.append(
                    CommitmentTrapRecord(
                        closure_probability=probability,
                        reliability_weight=weight,
                        planner=mode.value,
                        geometric_length=result.geometric_length,
                        uses_fragile_corridor=(4, 1) in result.path,
                        minimum_exact_return_probability=minimum_exact,
                        mean_exact_return_probability=mean_exact,
                        planning_time_ms=result.planning_time_ms,
                        nodes_expanded=result.nodes_expanded,
                    )
                )
    return records


def summarize_commitment_trap(
    records: list[CommitmentTrapRecord],
) -> dict[str, dict[str, float | int]]:
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[CommitmentTrapRecord]] = {}
    for row in records:
        grouped.setdefault(row.planner, []).append(row)

    result: dict[str, dict[str, float | int]] = {}
    for planner, rows in sorted(grouped.items()):
        result[planner] = {
            "trials": len(rows),
            "fragile_corridor_rate": sum(row.uses_fragile_corridor for row in rows) / len(rows),
            "mean_geometric_length": sum(row.geometric_length for row in rows) / len(rows),
            "mean_minimum_exact_return_probability": sum(
                row.minimum_exact_return_probability for row in rows
            )
            / len(rows),
            "mean_planning_time_ms": sum(row.planning_time_ms for row in rows) / len(rows),
        }
    return result


def write_commitment_trap_artifacts(
    records: list[CommitmentTrapRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_commitment_trap(records), handle, indent=2, sort_keys=True)
