"""Development pilot for proactive return-reliability-aware planning."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.experiments.recoverability_estimator_pilot import _scenario
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability


@dataclass(frozen=True)
class HazardPlannerPilotRecord:
    seed: int
    mode: str
    success: bool
    geometric_length: int
    planning_time_ms: float
    nodes_expanded: int
    minimum_exact_return_probability: float
    mean_exact_return_probability: float
    estimated_minimum_return_probability: float
    cumulative_return_fragility: float


def _condition_current_usable(
    hazard: TopologyHazardBelief,
    current: tuple[int, int],
) -> TopologyHazardBelief:
    return TopologyHazardBelief(
        {
            cell: probability
            for cell, probability in hazard.closure_probability.items()
            if cell != current
        }
    )


def run_hazard_planner_pilot(
    seeds: tuple[int, ...] = tuple(range(50)),
    *,
    hazard_count: int = 6,
    reliability_weight: float = 4.0,
) -> list[HazardPlannerPilotRecord]:
    if not seeds:
        raise ValueError("at least one development seed is required")
    if len(set(seeds)) != len(seeds):
        raise ValueError("development seeds must be unique")

    records: list[HazardPlannerPilotRecord] = []
    mission_start = (0, 0)
    mission_goal = (5, 5)
    mission_safe = {mission_start}
    config = HazardReliabilityAStarConfig(reliability_weight=reliability_weight)

    for seed in seeds:
        grid, hazard, _ = _scenario(seed, hazard_count=hazard_count)
        for mode in HazardReliabilityMode:
            result = hazard_reliability_astar(
                grid,
                mission_start,
                mission_goal,
                safe_cells=mission_safe,
                hazard=hazard,
                mode=mode,
                config=config,
            )
            if result.success:
                exact_values = [
                    exact_safe_return_probability(
                        grid,
                        cell,
                        mission_safe,
                        _condition_current_usable(hazard, cell),
                        max_hazard_cells=hazard_count,
                    )
                    for cell in result.path
                ]
                minimum_exact = min(exact_values)
                mean_exact = sum(exact_values) / len(exact_values)
            else:
                minimum_exact = 0.0
                mean_exact = 0.0
            records.append(
                HazardPlannerPilotRecord(
                    seed=seed,
                    mode=mode.value,
                    success=result.success,
                    geometric_length=result.geometric_length,
                    planning_time_ms=result.planning_time_ms,
                    nodes_expanded=result.nodes_expanded,
                    minimum_exact_return_probability=minimum_exact,
                    mean_exact_return_probability=mean_exact,
                    estimated_minimum_return_probability=result.minimum_estimated_return_probability,
                    cumulative_return_fragility=result.cumulative_return_fragility,
                )
            )
    return records


def summarize_hazard_planner_pilot(
    records: list[HazardPlannerPilotRecord],
) -> dict[str, dict[str, float | int]]:
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[HazardPlannerPilotRecord]] = {}
    for row in records:
        grouped.setdefault(row.mode, []).append(row)

    summary: dict[str, dict[str, float | int]] = {}
    for mode, rows in sorted(grouped.items()):
        successful = [row for row in rows if row.success]
        summary[mode] = {
            "trials": len(rows),
            "success_rate": sum(row.success for row in rows) / len(rows),
            "mean_geometric_length": (
                sum(row.geometric_length for row in successful) / len(successful)
                if successful
                else 0.0
            ),
            "mean_planning_time_ms": sum(row.planning_time_ms for row in rows) / len(rows),
            "mean_nodes_expanded": sum(row.nodes_expanded for row in rows) / len(rows),
            "mean_minimum_exact_return_probability": sum(
                row.minimum_exact_return_probability for row in rows
            )
            / len(rows),
            "mean_exact_return_probability": sum(row.mean_exact_return_probability for row in rows)
            / len(rows),
        }
    return summary


def write_hazard_planner_pilot_artifacts(
    records: list[HazardPlannerPilotRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_hazard_planner_pilot(records), handle, indent=2, sort_keys=True)
