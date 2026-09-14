"""Frozen geometric held-out benchmark for action-triggered return topology.

Unlike the repeated-module development family, these hand-built maps use
branching, L-shaped, and multi-trigger chamber geometries.  The scenarios are
fixed in source before CI execution.  The benchmark compares shortest-path,
state-only marginal-risk, and exact history-aware planning under common random
numbers.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.commitment_execution_benchmark import (
    _activated_indices,
    _realize_after_commitment,
    _state_only_marginal_hazard,
)
from dynnav.experiments.statistics import paired_binary_effect
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.recoverability import return_failure_probability


@dataclass(frozen=True)
class GeometricScenario:
    name: str
    grid: GridMap
    start: GridCell
    goal: GridCell
    safe: set[GridCell]
    model: CommitmentHazardModel


@dataclass(frozen=True)
class GeometricHeldoutRecord:
    scenario: str
    seed: int
    planner: str
    path_length: int
    activated_closure_count: int
    realized_closure_count: int
    final_return_probability: float
    irreversible_failure: bool


def _grid_from_free(width: int, height: int, free: set[GridCell]) -> GridMap:
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    return GridMap.from_obstacles(width, height, obstacles=obstacles)


def frozen_geometric_scenarios() -> tuple[GeometricScenario, ...]:
    """Return three geometrically distinct, predeclared evaluation maps."""
    # Fork: a short central branch activates a closure of the only bridge back
    # to the safe start; a longer upper branch avoids the trigger.
    free_fork = {
        (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2),
        (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
    }
    fork = GeometricScenario(
        name="fork",
        grid=_grid_from_free(7, 4, free_fork),
        start=(0, 2),
        goal=(6, 2),
        safe={(0, 2)},
        model=CommitmentHazardModel((
            CommitmentClosure(
                trigger=((4, 2), (5, 2)),
                closure_cell=(1, 2),
                closure_probability=0.80,
            ),
        )),
    )

    # L-room: the short lower/right route triggers a future bridge closure;
    # the upper-left arc reaches the same goal without that transition.
    free_l = {
        (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
        (5, 1), (5, 2), (5, 3),
        (2, 1), (2, 2), (2, 3), (3, 3), (4, 3),
        (3, 2),
    }
    l_room = GeometricScenario(
        name="l_room",
        grid=_grid_from_free(6, 4, free_l),
        start=(0, 0),
        goal=(5, 3),
        safe={(0, 0)},
        model=CommitmentHazardModel((
            CommitmentClosure(
                trigger=((5, 1), (5, 2)),
                closure_cell=(1, 0),
                closure_probability=0.75,
            ),
        )),
    )

    # Chamber: two shortcut transitions independently threaten two serial
    # return cells.  A perimeter route avoids both activations.
    free_chamber = {
        (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2),
        (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1),
        (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
    }
    chamber = GeometricScenario(
        name="chamber_two_trigger",
        grid=_grid_from_free(8, 3, free_chamber),
        start=(0, 2),
        goal=(7, 2),
        safe={(0, 2)},
        model=CommitmentHazardModel((
            CommitmentClosure(
                trigger=((4, 2), (5, 2)),
                closure_cell=(1, 2),
                closure_probability=0.65,
            ),
            CommitmentClosure(
                trigger=((5, 2), (6, 2)),
                closure_cell=(2, 2),
                closure_probability=0.70,
            ),
        )),
    )
    return fork, l_room, chamber


def run_geometric_heldout_benchmark(
    *,
    seeds: tuple[int, ...] = tuple(range(500)),
    recoverability_weight: float = 8.0,
) -> list[GeometricHeldoutRecord]:
    if not seeds:
        raise ValueError("seeds cannot be empty")
    records: list[GeometricHeldoutRecord] = []
    for scenario in frozen_geometric_scenarios():
        shortest = commitment_aware_astar(
            scenario.grid,
            scenario.start,
            scenario.goal,
            safe_cells=scenario.safe,
            hazard_model=scenario.model,
            mode=CommitmentPlannerMode.SHORTEST,
        )
        state_only = hazard_reliability_astar(
            scenario.grid,
            scenario.start,
            scenario.goal,
            safe_cells=scenario.safe,
            hazard=_state_only_marginal_hazard(scenario.model),
            mode=HazardReliabilityMode.SINGLE_RETURN,
            config=HazardReliabilityAStarConfig(
                reliability_weight=recoverability_weight
            ),
        )
        history = commitment_aware_astar(
            scenario.grid,
            scenario.start,
            scenario.goal,
            safe_cells=scenario.safe,
            hazard_model=scenario.model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
            config=CommitmentAwareAStarConfig(
                recoverability_weight=recoverability_weight,
                max_hazard_cells=16,
            ),
        )
        plans = {
            "shortest": shortest,
            "state_only_single": state_only,
            "history_exact": history,
        }
        for planner, result in plans.items():
            if not result.success:
                raise RuntimeError(
                    f"planner {planner} failed in geometric scenario {scenario.name}"
                )
            path = tuple(result.path)
            active = _activated_indices(scenario.model, path)
            final_return = float(getattr(result, "final_return_probability", float("nan")))
            for seed in seeds:
                updated, realized = _realize_after_commitment(
                    scenario.grid,
                    scenario.goal,
                    scenario.model,
                    active,
                    seed,
                )
                failure = return_failure_probability(
                    updated, scenario.goal, scenario.safe
                ) >= 1.0
                records.append(
                    GeometricHeldoutRecord(
                        scenario=scenario.name,
                        seed=seed,
                        planner=planner,
                        path_length=result.geometric_length,
                        activated_closure_count=len(active),
                        realized_closure_count=realized,
                        final_return_probability=final_return,
                        irreversible_failure=failure,
                    )
                )
    return records


def summarize_geometric_heldout(
    records: list[GeometricHeldoutRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    summary: dict[str, object] = {}
    for scenario in sorted({row.scenario for row in records}):
        scenario_rows = [row for row in records if row.scenario == scenario]
        planners = sorted({row.planner for row in scenario_rows})
        block: dict[str, object] = {}
        for planner in planners:
            rows = [row for row in scenario_rows if row.planner == planner]
            block[planner] = {
                "trials": len(rows),
                "path_length": rows[0].path_length,
                "activated_closure_count": rows[0].activated_closure_count,
                "irreversible_failure_rate": sum(
                    row.irreversible_failure for row in rows
                ) / len(rows),
            }
        baseline = {
            row.seed: row
            for row in scenario_rows
            if row.planner == "shortest"
        }
        effects: dict[str, object] = {}
        for planner in ("state_only_single", "history_exact"):
            candidate = {
                row.seed: row
                for row in scenario_rows
                if row.planner == planner
            }
            common = sorted(set(baseline) & set(candidate))
            effects[planner] = asdict(
                paired_binary_effect(
                    [baseline[seed].irreversible_failure for seed in common],
                    [candidate[seed].irreversible_failure for seed in common],
                    resamples=5000,
                    seed=2901 + len(scenario) + len(planner),
                )
            )
        block["paired_binary_effects_vs_shortest"] = effects
        summary[scenario] = block
    return summary


def write_geometric_heldout_artifacts(
    records: list[GeometricHeldoutRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_geometric_heldout(records),
            handle,
            indent=2,
            sort_keys=True,
        )
