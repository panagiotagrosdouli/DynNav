"""Scaling benchmark for exact versus non-enumerative history-aware planning."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.approx_commitment_aware_astar import (
    ApproxCommitmentAStarConfig,
    ApproxCommitmentMode,
    approx_commitment_aware_astar,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridMap


@dataclass(frozen=True)
class HistoryScalingRecord:
    hazard_count: int
    planner: str
    success: bool
    geometric_length: int
    planning_time_ms: float
    nodes_expanded: int
    final_return_probability: float
    minimum_return_probability: float


def forced_history_corridor(
    hazard_count: int,
    *,
    closure_probability: float = 0.1,
):
    """Build a one-cell-wide corridor whose forward motion activates hazards.

    Each trigger closes the cell immediately behind the robot with independent
    probability. The mission route is forced, so the endpoint accumulates
    ``hazard_count`` active events. This deliberately stresses exact outcome
    enumeration rather than route-choice combinatorics.
    """

    if hazard_count < 1:
        raise ValueError("hazard_count must be positive")
    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")

    width = hazard_count + 3
    grid = GridMap.from_obstacles(width, 1)
    start = (0, 0)
    goal = (width - 1, 0)
    closures = tuple(
        CommitmentClosure(
            trigger=((index + 1, 0), (index + 2, 0)),
            closure_cell=(index + 1, 0),
            closure_probability=closure_probability,
        )
        for index in range(hazard_count)
    )
    return grid, start, goal, CommitmentHazardModel(closures)


def run_history_scaling_benchmark(
    hazard_counts: tuple[int, ...] = (1, 2, 4, 6, 8, 10),
    *,
    closure_probability: float = 0.1,
) -> list[HistoryScalingRecord]:
    if not hazard_counts:
        raise ValueError("hazard_counts cannot be empty")

    records: list[HistoryScalingRecord] = []
    for count in hazard_counts:
        grid, start, goal, model = forced_history_corridor(
            int(count), closure_probability=closure_probability
        )
        exact = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
            config=CommitmentAwareAStarConfig(
                recoverability_weight=0.0,
                max_hazard_cells=max(hazard_counts),
            ),
        )
        records.append(
            HistoryScalingRecord(
                hazard_count=count,
                planner="exact",
                success=exact.success,
                geometric_length=exact.geometric_length,
                planning_time_ms=exact.planning_time_ms,
                nodes_expanded=exact.nodes_expanded,
                final_return_probability=exact.final_return_probability,
                minimum_return_probability=exact.minimum_return_probability,
            )
        )

        approximate = approx_commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            mode=ApproxCommitmentMode.REDUNDANT_RETURN,
            config=ApproxCommitmentAStarConfig(recoverability_weight=0.0),
        )
        records.append(
            HistoryScalingRecord(
                hazard_count=count,
                planner="approx_redundant",
                success=approximate.success,
                geometric_length=approximate.geometric_length,
                planning_time_ms=approximate.planning_time_ms,
                nodes_expanded=approximate.nodes_expanded,
                final_return_probability=approximate.final_estimated_return_probability,
                minimum_return_probability=approximate.minimum_estimated_return_probability,
            )
        )
    return records


def summarize_history_scaling(
    records: list[HistoryScalingRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    exact = {row.hazard_count: row for row in records if row.planner == "exact"}
    approx = {row.hazard_count: row for row in records if row.planner == "approx_redundant"}
    counts = sorted(set(exact) & set(approx))
    return {
        "hazard_counts": counts,
        "exact_max_planning_time_ms": max(exact[count].planning_time_ms for count in counts),
        "approx_max_planning_time_ms": max(approx[count].planning_time_ms for count in counts),
        "max_probability_absolute_error": max(
            abs(exact[count].final_return_probability - approx[count].final_return_probability)
            for count in counts
        ),
        "per_count": {
            str(count): {
                "exact_planning_time_ms": exact[count].planning_time_ms,
                "approx_planning_time_ms": approx[count].planning_time_ms,
                "planning_time_ratio_exact_over_approx": (
                    exact[count].planning_time_ms / approx[count].planning_time_ms
                    if approx[count].planning_time_ms > 0.0
                    else None
                ),
                "probability_absolute_error": abs(
                    exact[count].final_return_probability
                    - approx[count].final_return_probability
                ),
            }
            for count in counts
        },
    }


def write_history_scaling_artifacts(
    records: list[HistoryScalingRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_history_scaling(records), handle, indent=2, sort_keys=True)
