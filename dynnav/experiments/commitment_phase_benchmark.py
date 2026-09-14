"""Analytic phase-boundary benchmark for history-conditioned commitment planning."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class CommitmentPhaseRecord:
    detour_depth: int
    closure_probability: float
    recoverability_weight: float
    planner: str
    geometric_length: int
    activated_closure_count: int
    final_return_probability: float
    chose_detour: bool
    analytic_detour_expected: bool
    matches_analytic_boundary: bool
    planning_time_ms: float
    nodes_expanded: int


def commitment_phase_world(
    detour_depth: int,
    closure_probability: float,
) -> tuple[GridMap, GridCell, GridCell, set[GridCell], CommitmentHazardModel]:
    """Create one risky terminal commitment and a uniquely sized safe detour.

    The start reaches the right-hand region through a sole return bridge and
    then a junction. The geometrically direct route crosses a midpoint and its
    final midpoint-to-goal transition activates a possible future closure of
    that bridge.

    The safe alternative is a U-shaped corridor: from the junction it moves
    ``detour_depth`` cells upward, crosses once, then moves the same distance
    downward to the goal. Its overhead over the direct route is exactly
    ``2 * detour_depth``. The middle column is blocked away from its two
    intended crossings, so no intermediate-row shortcut exists.

    Placing the trigger on the terminal direct transition is deliberate: the
    planner's objective charges ``lambda * (1 - P(return))`` after every
    transition. A terminal trigger therefore contributes exactly one
    ``lambda * p`` term, making the controlled switch boundary
    ``lambda * p > 2 * detour_depth`` identifiable rather than accidentally
    multiplying the penalty by the number of post-trigger steps.
    """
    if detour_depth < 1:
        raise ValueError("detour_depth must be at least 1")
    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")

    d = detour_depth
    width, height = 5, d + 1
    start = (0, d)
    bridge = (1, d)
    junction = (2, d)
    goal = (4, d)
    trigger_midpoint = (3, d)

    free: set[GridCell] = {start, bridge, junction, trigger_midpoint, goal}
    free.update((2, y) for y in range(0, d + 1))
    free.update((4, y) for y in range(0, d + 1))
    free.add((3, 0))
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=(trigger_midpoint, goal),
                closure_cell=bridge,
                closure_probability=closure_probability,
            ),
        )
    )
    return grid, start, goal, {start}, model


def run_commitment_phase_benchmark(
    *,
    detour_depths: tuple[int, ...] = (1, 2, 3),
    closure_probabilities: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9),
    recoverability_weights: tuple[float, ...] = (1.0, 2.0, 4.0, 8.0, 16.0),
) -> list[CommitmentPhaseRecord]:
    if not detour_depths or not closure_probabilities or not recoverability_weights:
        raise ValueError("benchmark axes must be non-empty")
    records: list[CommitmentPhaseRecord] = []

    for depth in detour_depths:
        for probability in closure_probabilities:
            grid, start, goal, safe, model = commitment_phase_world(depth, probability)
            for weight in recoverability_weights:
                analytic = weight * probability > 2.0 * depth
                for mode in (CommitmentPlannerMode.SHORTEST, CommitmentPlannerMode.HISTORY_AWARE):
                    result = commitment_aware_astar(
                        grid,
                        start,
                        goal,
                        safe_cells=safe,
                        hazard_model=model,
                        mode=mode,
                        config=CommitmentAwareAStarConfig(recoverability_weight=weight),
                    )
                    chose_detour = result.activated_closure_count == 0
                    expected = False if mode is CommitmentPlannerMode.SHORTEST else analytic
                    records.append(
                        CommitmentPhaseRecord(
                            detour_depth=depth,
                            closure_probability=probability,
                            recoverability_weight=weight,
                            planner=mode.value,
                            geometric_length=result.geometric_length,
                            activated_closure_count=result.activated_closure_count,
                            final_return_probability=result.final_return_probability,
                            chose_detour=chose_detour,
                            analytic_detour_expected=expected,
                            matches_analytic_boundary=(chose_detour == expected),
                            planning_time_ms=result.planning_time_ms,
                            nodes_expanded=result.nodes_expanded,
                        )
                    )
    return records


def summarize_commitment_phase(records: list[CommitmentPhaseRecord]) -> dict[str, dict[str, float | int]]:
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[CommitmentPhaseRecord]] = {}
    for row in records:
        grouped.setdefault(row.planner, []).append(row)
    return {
        planner: {
            "trials": len(rows),
            "detour_rate": sum(row.chose_detour for row in rows) / len(rows),
            "analytic_boundary_match_rate": sum(row.matches_analytic_boundary for row in rows) / len(rows),
            "mean_final_return_probability": sum(row.final_return_probability for row in rows) / len(rows),
            "mean_geometric_length": sum(row.geometric_length for row in rows) / len(rows),
            "mean_planning_time_ms": sum(row.planning_time_ms for row in rows) / len(rows),
        }
        for planner, rows in sorted(grouped.items())
    }


def write_commitment_phase_artifacts(records: list[CommitmentPhaseRecord], output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_commitment_phase(records), handle, indent=2, sort_keys=True)
