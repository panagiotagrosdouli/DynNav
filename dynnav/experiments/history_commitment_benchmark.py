"""Phase benchmark for history-conditioned commitment-aware planning."""

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
from dynnav.planners.grid_map import GridMap


@dataclass(frozen=True)
class HistoryCommitmentRecord:
    closure_probability: float
    recoverability_weight: float
    mode: str
    success: bool
    geometric_length: int
    activated_closure_count: int
    final_return_probability: float
    minimum_return_probability: float
    cumulative_return_fragility: float
    planning_time_ms: float
    nodes_expanded: int


def history_commitment_world(probability: float):
    """Return a controlled world with a risky direct trigger and safe detour.

    The only bridge from the right region back to the launch-safe region is
    (1, 1). The direct transition from (2, 1) to the goal (3, 1) activates a
    possible future closure of that bridge. A two-step detour through either
    side of the right loop reaches the same goal without activating the event.
    """

    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    start = (0, 1)
    goal = (3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 1), (3, 1)),
                closure_cell=(1, 1),
                closure_probability=probability,
            ),
        )
    )
    return grid, start, goal, model


def _record(probability: float, weight: float, result) -> HistoryCommitmentRecord:
    return HistoryCommitmentRecord(
        closure_probability=float(probability),
        recoverability_weight=float(weight),
        mode=result.mode.value,
        success=result.success,
        geometric_length=result.geometric_length,
        activated_closure_count=result.activated_closure_count,
        final_return_probability=result.final_return_probability,
        minimum_return_probability=result.minimum_return_probability,
        cumulative_return_fragility=result.cumulative_return_fragility,
        planning_time_ms=result.planning_time_ms,
        nodes_expanded=result.nodes_expanded,
    )


def run_history_commitment_benchmark(
    closure_probabilities: tuple[float, ...] = (0.05, 0.2, 0.4, 0.6, 0.8, 0.95),
    recoverability_weights: tuple[float, ...] = (0.5, 1.0, 2.0, 4.0, 8.0),
) -> list[HistoryCommitmentRecord]:
    if not closure_probabilities or not recoverability_weights:
        raise ValueError("probabilities and weights must be non-empty")

    records: list[HistoryCommitmentRecord] = []
    for probability in closure_probabilities:
        grid, start, goal, model = history_commitment_world(float(probability))

        shortest = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            mode=CommitmentPlannerMode.SHORTEST,
        )
        records.append(_record(probability, 0.0, shortest))

        for weight in recoverability_weights:
            result = commitment_aware_astar(
                grid,
                start,
                goal,
                safe_cells={start},
                hazard_model=model,
                mode=CommitmentPlannerMode.HISTORY_AWARE,
                config=CommitmentAwareAStarConfig(recoverability_weight=float(weight)),
            )
            records.append(_record(probability, weight, result))
    return records


def summarize_history_commitment(
    records: list[HistoryCommitmentRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    history = [row for row in records if row.mode == CommitmentPlannerMode.HISTORY_AWARE.value]
    shortest = [row for row in records if row.mode == CommitmentPlannerMode.SHORTEST.value]
    detours = [row for row in history if row.geometric_length > 3]
    thresholds: dict[str, float | None] = {}
    for weight in sorted({row.recoverability_weight for row in history}):
        rows = sorted(
            (row for row in history if row.recoverability_weight == weight),
            key=lambda row: row.closure_probability,
        )
        first_detour = next((row.closure_probability for row in rows if row.geometric_length > 3), None)
        thresholds[str(weight)] = first_detour
    return {
        "trials": len(records),
        "probability_levels": len({row.closure_probability for row in records}),
        "weight_levels": len({row.recoverability_weight for row in history}),
        "history_aware_detour_rate": len(detours) / len(history),
        "history_aware_mean_path_length": sum(row.geometric_length for row in history) / len(history),
        "shortest_mean_path_length": sum(row.geometric_length for row in shortest) / len(shortest),
        "history_aware_mean_minimum_return_probability": sum(
            row.minimum_return_probability for row in history
        )
        / len(history),
        "shortest_mean_minimum_return_probability": sum(
            row.minimum_return_probability for row in shortest
        )
        / len(shortest),
        "history_aware_mean_return_probability": sum(row.final_return_probability for row in history)
        / len(history),
        "shortest_mean_return_probability": sum(row.final_return_probability for row in shortest)
        / len(shortest),
        "detour_threshold_by_weight": thresholds,
    }


def write_history_commitment_artifacts(
    records: list[HistoryCommitmentRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_history_commitment(records), handle, indent=2, sort_keys=True)
