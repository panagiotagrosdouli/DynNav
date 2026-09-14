"""Frozen soft-vs-hard Pareto sweep on geometric held-out worlds."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.experiments.commitment_execution_benchmark import (
    _activated_indices,
    _realize_after_commitment,
)
from dynnav.experiments.geometric_heldout_benchmark import frozen_geometric_scenarios
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.commitment_safe_return_astar import (
    SafeReturnConstraintConfig,
    commitment_safe_return_astar,
)
from dynnav.recoverability import return_failure_probability

SOFT_WEIGHTS: tuple[float, ...] = (0.0, 1.0, 2.0, 4.0, 8.0, 16.0)
HARD_THRESHOLDS: tuple[float, ...] = (0.50, 0.70, 0.80, 0.90, 0.95, 0.99)


@dataclass(frozen=True)
class GeometricParetoRecord:
    scenario: str
    family: str
    parameter: float
    seed: int
    planner_success: bool
    path_length: int | None
    activated_closure_count: int | None
    final_return_probability: float | None
    minimum_return_probability: float | None
    planning_time_ms: float
    nodes_expanded: int
    irreversible_failure: bool | None


def run_geometric_pareto_benchmark(
    *,
    seeds: tuple[int, ...] = tuple(range(500)),
    soft_weights: tuple[float, ...] = SOFT_WEIGHTS,
    hard_thresholds: tuple[float, ...] = HARD_THRESHOLDS,
) -> list[GeometricParetoRecord]:
    """Evaluate the predeclared soft and hard parameter grids.

    Planning infeasibility is kept separate from post-closure irreversible
    failure. Common random numbers are preserved through the existing
    seed-indexed closure-event realization helper.
    """
    if not seeds:
        raise ValueError("seeds cannot be empty")
    if not soft_weights or not hard_thresholds:
        raise ValueError("parameter grids cannot be empty")

    records: list[GeometricParetoRecord] = []
    for scenario in frozen_geometric_scenarios():
        plans: list[tuple[str, float, object]] = []
        for weight in soft_weights:
            plans.append(
                (
                    "soft_history",
                    weight,
                    commitment_aware_astar(
                        scenario.grid,
                        scenario.start,
                        scenario.goal,
                        safe_cells=scenario.safe,
                        hazard_model=scenario.model,
                        mode=CommitmentPlannerMode.HISTORY_AWARE,
                        config=CommitmentAwareAStarConfig(
                            recoverability_weight=weight,
                            max_hazard_cells=16,
                        ),
                    ),
                )
            )
        for threshold in hard_thresholds:
            plans.append(
                (
                    "hard_return",
                    threshold,
                    commitment_safe_return_astar(
                        scenario.grid,
                        scenario.start,
                        scenario.goal,
                        safe_cells=scenario.safe,
                        hazard_model=scenario.model,
                        config=SafeReturnConstraintConfig(
                            minimum_return_probability=threshold,
                            max_hazard_cells=16,
                        ),
                    ),
                )
            )

        for family, parameter, result in plans:
            success = bool(result.success)
            if success:
                path = tuple(result.path)
                active = _activated_indices(scenario.model, path)
                path_length: int | None = int(result.geometric_length)
                activated_count: int | None = len(active)
                final_return: float | None = float(result.final_return_probability)
                minimum_return: float | None = float(result.minimum_return_probability)
            else:
                active = frozenset()
                path_length = None
                activated_count = None
                final_return = None
                minimum_return = None

            for seed in seeds:
                failure: bool | None = None
                if success:
                    updated, _ = _realize_after_commitment(
                        scenario.grid,
                        scenario.goal,
                        scenario.model,
                        active,
                        seed,
                    )
                    failure = (
                        return_failure_probability(updated, scenario.goal, scenario.safe)
                        >= 1.0
                    )
                records.append(
                    GeometricParetoRecord(
                        scenario=scenario.name,
                        family=family,
                        parameter=parameter,
                        seed=seed,
                        planner_success=success,
                        path_length=path_length,
                        activated_closure_count=activated_count,
                        final_return_probability=final_return,
                        minimum_return_probability=minimum_return,
                        planning_time_ms=float(result.planning_time_ms),
                        nodes_expanded=int(result.nodes_expanded),
                        irreversible_failure=failure,
                    )
                )
    return records


def summarize_geometric_pareto(
    records: list[GeometricParetoRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")

    summary: dict[str, object] = {}
    for scenario in sorted({row.scenario for row in records}):
        scenario_rows = [row for row in records if row.scenario == scenario]
        entries: list[dict[str, object]] = []
        keys = sorted({(row.family, row.parameter) for row in scenario_rows})
        for family, parameter in keys:
            rows = [
                row
                for row in scenario_rows
                if row.family == family and row.parameter == parameter
            ]
            first = rows[0]
            success = first.planner_success
            execution = [
                row.irreversible_failure
                for row in rows
                if row.irreversible_failure is not None
            ]
            entries.append(
                {
                    "family": family,
                    "parameter": parameter,
                    "trials": len(rows),
                    "planner_success": success,
                    "path_length": first.path_length,
                    "activated_closure_count": first.activated_closure_count,
                    "final_return_probability": first.final_return_probability,
                    "minimum_return_probability": first.minimum_return_probability,
                    "planning_time_ms": first.planning_time_ms,
                    "nodes_expanded": first.nodes_expanded,
                    "execution_trials": len(execution),
                    "irreversible_failure_rate": (
                        sum(bool(value) for value in execution) / len(execution)
                        if execution
                        else None
                    ),
                }
            )
        summary[scenario] = entries
    return summary


def write_geometric_pareto_artifacts(
    records: list[GeometricParetoRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_geometric_pareto(records),
            handle,
            indent=2,
            sort_keys=True,
        )
