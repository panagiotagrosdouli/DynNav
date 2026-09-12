"""Planner-level counterexample for the individually-critical cut approximation."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import (
    CommitmentClosure,
    CommitmentHazardModel,
    exact_history_conditioned_return_probability,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.commitment_cut_astar import (
    CommitmentCutAStarConfig,
    commitment_cut_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class JointCutRecord:
    closure_probability: float
    recoverability_weight: float
    planner: str
    path_length: int
    activated_closure_count: int
    final_exact_return_probability: float
    final_cut_return_estimate: float


def joint_cut_world(
    closure_probability: float,
) -> tuple[GridMap, GridCell, GridCell, set[GridCell], CommitmentHazardModel]:
    """Two parallel return corridors whose hazards disconnect only jointly.

    The direct two-edge outbound route activates one hazard in each parallel
    return corridor. A two-step-longer upper detour reaches the same goal while
    activating neither event. Removing either hazard cell alone leaves one
    return corridor, so the individually-critical cut approximation reports
    full reliability even after both hazards are active.
    """
    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")

    width, height = 5, 5
    free: set[GridCell] = {
        (0, 2),
        (0, 1), (1, 1), (2, 1),
        (0, 3), (1, 3), (2, 3),
        (2, 2), (3, 2), (4, 2),
        (3, 1), (4, 1),
    }
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    start = (0, 2)
    goal = (4, 2)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 2), (3, 2)),
                closure_cell=(1, 1),
                closure_probability=closure_probability,
            ),
            CommitmentClosure(
                trigger=((3, 2), (4, 2)),
                closure_cell=(1, 3),
                closure_probability=closure_probability,
            ),
        )
    )
    return grid, start, goal, {start}, model


def _exact_final_probability(
    grid: GridMap,
    path: tuple[GridCell, ...],
    safe: set[GridCell],
    model: CommitmentHazardModel,
) -> float:
    return exact_history_conditioned_return_probability(
        grid,
        path,
        safe,
        model,
        max_hazard_cells=16,
    )


def run_joint_cut_counterexample(
    *,
    closure_probabilities: tuple[float, ...] = (0.2, 0.5, 0.8),
    recoverability_weights: tuple[float, ...] = (2.0, 4.0, 8.0),
) -> list[JointCutRecord]:
    records: list[JointCutRecord] = []
    for probability in closure_probabilities:
        grid, start, goal, safe, model = joint_cut_world(probability)
        for weight in recoverability_weights:
            exact = commitment_aware_astar(
                grid,
                start,
                goal,
                safe_cells=safe,
                hazard_model=model,
                mode=CommitmentPlannerMode.HISTORY_AWARE,
                config=CommitmentAwareAStarConfig(
                    recoverability_weight=weight,
                    max_hazard_cells=16,
                ),
            )
            cut = commitment_cut_astar(
                grid,
                start,
                goal,
                safe_cells=safe,
                hazard_model=model,
                config=CommitmentCutAStarConfig(recoverability_weight=weight),
            )
            exact_probability = _exact_final_probability(
                grid, tuple(exact.path), safe, model
            )
            cut_exact_probability = _exact_final_probability(
                grid, tuple(cut.path), safe, model
            )
            records.append(
                JointCutRecord(
                    closure_probability=probability,
                    recoverability_weight=weight,
                    planner="history_exact",
                    path_length=exact.geometric_length,
                    activated_closure_count=exact.activated_closure_count,
                    final_exact_return_probability=exact_probability,
                    final_cut_return_estimate=exact_probability,
                )
            )
            records.append(
                JointCutRecord(
                    closure_probability=probability,
                    recoverability_weight=weight,
                    planner="history_cut",
                    path_length=cut.geometric_length,
                    activated_closure_count=cut.activated_closure_count,
                    final_exact_return_probability=cut_exact_probability,
                    final_cut_return_estimate=cut.final_return_upper_bound,
                )
            )
    return records


def summarize_joint_cut_counterexample(records: list[JointCutRecord]) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    paired = []
    for exact in (row for row in records if row.planner == "history_exact"):
        cut = next(
            row
            for row in records
            if row.planner == "history_cut"
            and row.closure_probability == exact.closure_probability
            and row.recoverability_weight == exact.recoverability_weight
        )
        paired.append((exact, cut))
    return {
        "trials": len(records),
        "route_disagreement_rate": sum(
            exact.path_length != cut.path_length
            or exact.activated_closure_count != cut.activated_closure_count
            for exact, cut in paired
        ) / len(paired),
        "cut_optimism_cases": sum(
            cut.final_cut_return_estimate > cut.final_exact_return_probability
            for _, cut in paired
        ),
        "pairs": [
            {
                "closure_probability": exact.closure_probability,
                "recoverability_weight": exact.recoverability_weight,
                "exact_path_length": exact.path_length,
                "cut_path_length": cut.path_length,
                "exact_activated_closures": exact.activated_closure_count,
                "cut_activated_closures": cut.activated_closure_count,
                "cut_exact_return_probability": cut.final_exact_return_probability,
                "cut_return_estimate": cut.final_cut_return_estimate,
            }
            for exact, cut in paired
        ],
    }


def write_joint_cut_counterexample_artifacts(
    records: list[JointCutRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_joint_cut_counterexample(records), handle, indent=2, sort_keys=True)
