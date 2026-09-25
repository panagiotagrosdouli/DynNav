"""Frozen generated benchmark where every feasible route activates a hazard.

The benchmark addresses a key validity concern in the original mechanism
experiments: a history-aware planner should not be able to win merely by taking
a trigger-free route.  Here the goal has exactly two incoming transitions and
both are triggers.  The short route activates one return-critical closure and
the longer route activates another.  Both closure cells lie on the common
return corridor, so route choice changes which stochastic commitment is active.

Scenario parameters are generated deterministically from a frozen seed before
outcomes are evaluated.
"""
from __future__ import annotations

import csv
import json
import random
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

FROZEN_GENERATOR_SEED = 260925
FROZEN_SCENARIO_COUNT = 40


@dataclass(frozen=True)
class ForcedHazardSpec:
    scenario_id: int
    detour_depth: int
    direct_probability: float
    detour_probability: float


@dataclass(frozen=True)
class ForcedHazardRecord:
    scenario_id: int
    trial_seed: int
    detour_depth: int
    direct_probability: float
    detour_probability: float
    planner: str
    path_length: int
    activated_hazard: int
    activated_probability: float
    analytic_detour_expected: bool
    chose_detour: bool
    postclosure_return_infeasible: bool


def frozen_forced_hazard_specs(
    *,
    count: int = FROZEN_SCENARIO_COUNT,
    seed: int = FROZEN_GENERATOR_SEED,
) -> tuple[ForcedHazardSpec, ...]:
    """Generate the frozen scenario suite without inspecting planner outcomes."""
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    specs: list[ForcedHazardSpec] = []
    for scenario_id in range(count):
        specs.append(
            ForcedHazardSpec(
                scenario_id=scenario_id,
                detour_depth=rng.randint(1, 4),
                direct_probability=round(rng.uniform(0.05, 0.95), 2),
                detour_probability=round(rng.uniform(0.05, 0.95), 2),
            )
        )
    return tuple(specs)


def forced_hazard_world(
    spec: ForcedHazardSpec,
) -> tuple[GridMap, GridCell, GridCell, set[GridCell], CommitmentHazardModel]:
    """Create two route choices, each with an unavoidable terminal trigger."""
    d = spec.detour_depth
    if d < 1:
        raise ValueError("detour_depth must be positive")
    for value in (spec.direct_probability, spec.detour_probability):
        if not 0.0 <= value <= 1.0:
            raise ValueError("closure probabilities must lie in [0, 1]")

    width = 8
    main_y = d
    start = (0, main_y)
    goal = (7, main_y)

    # Common prefix and short direct branch.
    free: set[GridCell] = {(x, main_y) for x in range(width)}
    # Longer upper branch leaves at x=3 and rejoins only at the goal.
    free.update((3, y) for y in range(main_y + 1))
    free.update((x, 0) for x in range(3, width))
    free.update((7, y) for y in range(main_y + 1))

    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(main_y + 1)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, main_y + 1, obstacles=obstacles)

    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((6, main_y), goal),
                closure_cell=(1, main_y),
                closure_probability=spec.direct_probability,
            ),
            CommitmentClosure(
                trigger=((7, main_y - 1), goal),
                closure_cell=(2, main_y),
                closure_probability=spec.detour_probability,
            ),
        )
    )
    return grid, start, goal, {start}, model


def run_forced_hazard_choice_benchmark(
    *,
    specs: tuple[ForcedHazardSpec, ...] | None = None,
    trial_seeds: tuple[int, ...] = tuple(range(200)),
    recoverability_weight: float = 8.0,
) -> list[ForcedHazardRecord]:
    """Evaluate shortest, exact state-only, and exact history-aware planning."""
    if not trial_seeds:
        raise ValueError("trial_seeds cannot be empty")
    frozen = frozen_forced_hazard_specs() if specs is None else specs
    if not frozen:
        raise ValueError("specs cannot be empty")

    records: list[ForcedHazardRecord] = []
    for spec in frozen:
        grid, start, goal, safe, model = forced_hazard_world(spec)

        shortest = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            mode=CommitmentPlannerMode.SHORTEST,
        )
        state_only_exact = hazard_reliability_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard=_state_only_marginal_hazard(model),
            mode=HazardReliabilityMode.EXACT_RETURN,
            config=HazardReliabilityAStarConfig(
                reliability_weight=recoverability_weight,
                max_hazard_cells=16,
            ),
        )
        history_exact = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
            config=CommitmentAwareAStarConfig(
                recoverability_weight=recoverability_weight,
                max_hazard_cells=16,
            ),
        )

        plans = {
            "shortest": shortest,
            "state_only_exact": state_only_exact,
            "history_exact": history_exact,
        }
        analytic_detour = (
            recoverability_weight
            * (spec.direct_probability - spec.detour_probability)
            > 2.0 * spec.detour_depth
        )

        for planner, result in plans.items():
            if not result.success:
                raise RuntimeError(
                    f"planner {planner} failed in forced-hazard scenario {spec.scenario_id}"
                )
            path = tuple(result.path)
            active = sorted(_activated_indices(model, path))
            if len(active) != 1:
                raise RuntimeError(
                    "every successful route must activate exactly one terminal hazard; "
                    f"planner={planner}, scenario={spec.scenario_id}, active={active}"
                )
            active_index = active[0]
            active_probability = model.closures[active_index].closure_probability
            chose_detour = active_index == 1

            for trial_seed in trial_seeds:
                latent_seed = spec.scenario_id * 1_000_003 + trial_seed
                updated, _ = _realize_after_commitment(
                    grid,
                    goal,
                    model,
                    {active_index},
                    latent_seed,
                )
                failed = return_failure_probability(updated, goal, safe) >= 1.0
                records.append(
                    ForcedHazardRecord(
                        scenario_id=spec.scenario_id,
                        trial_seed=trial_seed,
                        detour_depth=spec.detour_depth,
                        direct_probability=spec.direct_probability,
                        detour_probability=spec.detour_probability,
                        planner=planner,
                        path_length=result.geometric_length,
                        activated_hazard=active_index,
                        activated_probability=active_probability,
                        analytic_detour_expected=analytic_detour,
                        chose_detour=chose_detour,
                        postclosure_return_infeasible=failed,
                    )
                )
    return records


def summarize_forced_hazard_choice(
    records: list[ForcedHazardRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")

    planners = sorted({row.planner for row in records})
    summary: dict[str, object] = {
        "scenario_count": len({row.scenario_id for row in records}),
        "trial_count_per_planner": len(records) // len(planners),
        "planners": {},
    }
    planner_block: dict[str, object] = {}
    for planner in planners:
        rows = [row for row in records if row.planner == planner]
        by_scenario = {
            row.scenario_id: row
            for row in rows
            if row.trial_seed == min(r.trial_seed for r in rows)
        }
        planner_block[planner] = {
            "postclosure_return_infeasible_rate": sum(
                row.postclosure_return_infeasible for row in rows
            )
            / len(rows),
            "mean_activated_probability": sum(row.activated_probability for row in rows)
            / len(rows),
            "mean_path_length": sum(row.path_length for row in by_scenario.values())
            / len(by_scenario),
            "detour_scenario_count": sum(
                row.chose_detour for row in by_scenario.values()
            ),
        }
    summary["planners"] = planner_block

    index = {
        (row.planner, row.scenario_id, row.trial_seed): row
        for row in records
    }
    keys = sorted(
        (row.scenario_id, row.trial_seed)
        for row in records
        if row.planner == "state_only_exact"
    )
    state_only = [
        index[("state_only_exact", scenario_id, seed)].postclosure_return_infeasible
        for scenario_id, seed in keys
    ]
    history = [
        index[("history_exact", scenario_id, seed)].postclosure_return_infeasible
        for scenario_id, seed in keys
    ]
    summary["history_vs_state_only_exact"] = asdict(
        paired_binary_effect(
            state_only,
            history,
            resamples=5000,
            seed=FROZEN_GENERATOR_SEED,
        )
    )

    history_scenario_rows = {
        row.scenario_id: row
        for row in records
        if row.planner == "history_exact" and row.trial_seed == 0
    }
    summary["history_analytic_route_match_rate"] = sum(
        row.chose_detour == row.analytic_detour_expected
        for row in history_scenario_rows.values()
    ) / len(history_scenario_rows)
    summary["history_differs_from_state_only_scenarios"] = sum(
        history_scenario_rows[scenario_id].activated_hazard
        != index[("state_only_exact", scenario_id, 0)].activated_hazard
        for scenario_id in history_scenario_rows
    )
    return summary


def write_forced_hazard_choice_artifacts(
    records: list[ForcedHazardRecord],
    output_dir: str | Path,
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_forced_hazard_choice(records),
            handle,
            indent=2,
            sort_keys=True,
        )
    with (target / "scenario_specs.json").open("w", encoding="utf-8") as handle:
        specs = {
            row.scenario_id: {
                "detour_depth": row.detour_depth,
                "direct_probability": row.direct_probability,
                "detour_probability": row.detour_probability,
            }
            for row in records
            if row.planner == "shortest" and row.trial_seed == 0
        }
        json.dump(specs, handle, indent=2, sort_keys=True)
