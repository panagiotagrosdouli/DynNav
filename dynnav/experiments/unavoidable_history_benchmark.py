"""Frozen reviewer-challenge benchmark with unavoidable action-triggered hazards.

Every start-to-goal path must activate at least one hazard per module. This
removes the easiest regime in the original controlled worlds, where a planner
could avoid every trigger and therefore reduce the declared post-closure risk
to zero by construction.

The suite is deterministic from a committed seed. Scenario generation is frozen
before outcome inspection; results should enter the paper only from a retained
artifact produced from the exact commit under review.
"""
from __future__ import annotations

import argparse
import csv
import heapq
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

FROZEN_GENERATOR_SEED = 20260925
FROZEN_SCENARIO_COUNT = 24
FROZEN_EXECUTION_SEEDS = tuple(range(500))
PROBABILITY_CHOICES = (0.15, 0.25, 0.35, 0.5, 0.65, 0.75, 0.85)


@dataclass(frozen=True)
class UnavoidableScenario:
    name: str
    grid: GridMap
    start: GridCell
    goal: GridCell
    safe: set[GridCell]
    model: CommitmentHazardModel
    module_count: int
    detour_depths: tuple[int, ...]
    detour_directions: tuple[int, ...]


@dataclass(frozen=True)
class UnavoidableRecord:
    scenario: str
    seed: int
    planner: str
    path_length: int
    activated_closure_count: int
    realized_closure_count: int
    final_exact_return_probability: float
    return_infeasible: bool


def unavoidable_choice_world(
    *,
    direct_probabilities: tuple[float, ...],
    detour_probabilities: tuple[float, ...],
    detour_depths: tuple[int, ...],
    detour_directions: tuple[int, ...],
    name: str = "unavoidable",
) -> UnavoidableScenario:
    """Create serial choice modules where every route activates one hazard.

    Each module has two return-critical cells on the common stem, followed by a
    binary route choice. The short branch activates a future closure of one
    critical cell; the longer branch activates a different critical cell. Both
    alternatives therefore retain stochastic return risk. No trigger-free
    start-to-goal route exists.
    """
    n = len(direct_probabilities)
    if n < 1:
        raise ValueError("at least one module is required")
    if not (
        len(detour_probabilities) == n
        and len(detour_depths) == n
        and len(detour_directions) == n
    ):
        raise ValueError("all per-module parameter tuples must have equal length")
    if any(p < 0.0 or p > 1.0 for p in direct_probabilities + detour_probabilities):
        raise ValueError("closure probabilities must be in [0, 1]")
    if any(depth < 1 or depth > 3 for depth in detour_depths):
        raise ValueError("detour depths must be in [1, 3]")
    if any(direction not in (-1, 1) for direction in detour_directions):
        raise ValueError("detour directions must be -1 or 1")

    max_depth = max(detour_depths)
    main_y = max_depth
    height = 2 * max_depth + 1
    width = 5 * n + 1
    free: set[GridCell] = {(x, main_y) for x in range(width)}
    closures: list[CommitmentClosure] = []

    for index, (p_direct, p_detour, depth, direction) in enumerate(
        zip(
            direct_probabilities,
            detour_probabilities,
            detour_depths,
            detour_directions,
            strict=True,
        )
    ):
        base = 5 * index
        critical_a = (base + 1, main_y)
        critical_b = (base + 2, main_y)
        source = (base + 3, main_y)
        direct_mid = (base + 4, main_y)
        target = (base + 5, main_y)
        detour_y = main_y + direction * depth

        # The alternative branch leaves the common source vertically, crosses
        # two columns, and rejoins at the common target.
        step = 1 if detour_y > main_y else -1
        for y in range(main_y, detour_y + step, step):
            free.add((source[0], y))
            free.add((target[0], y))
        free.add((direct_mid[0], detour_y))

        closures.extend(
            (
                CommitmentClosure(
                    trigger=(source, direct_mid),
                    closure_cell=critical_a,
                    closure_probability=p_direct,
                ),
                CommitmentClosure(
                    trigger=(source, (source[0], main_y + direction)),
                    closure_cell=critical_b,
                    closure_probability=p_detour,
                ),
            )
        )

    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    start = (0, main_y)
    goal = (width - 1, main_y)
    scenario = UnavoidableScenario(
        name=name,
        grid=grid,
        start=start,
        goal=goal,
        safe={start},
        model=CommitmentHazardModel(tuple(closures)),
        module_count=n,
        detour_depths=detour_depths,
        detour_directions=detour_directions,
    )
    scenario.model.validate(grid)
    return scenario


def frozen_unavoidable_scenarios(
    *,
    seed: int = FROZEN_GENERATOR_SEED,
    count: int = FROZEN_SCENARIO_COUNT,
) -> tuple[UnavoidableScenario, ...]:
    """Generate the committed challenge suite deterministically."""
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    scenarios: list[UnavoidableScenario] = []
    for index in range(count):
        modules = rng.randint(1, 4)
        direct: list[float] = []
        detour: list[float] = []
        depths: list[int] = []
        directions: list[int] = []
        for _ in range(modules):
            p_direct = rng.choice(PROBABILITY_CHOICES)
            alternatives = tuple(
                value for value in PROBABILITY_CHOICES if abs(value - p_direct) >= 0.20
            )
            p_detour = rng.choice(alternatives)
            direct.append(p_direct)
            detour.append(p_detour)
            depths.append(rng.randint(1, 3))
            directions.append(rng.choice((-1, 1)))
        scenarios.append(
            unavoidable_choice_world(
                direct_probabilities=tuple(direct),
                detour_probabilities=tuple(detour),
                detour_depths=tuple(depths),
                detour_directions=tuple(directions),
                name=f"frozen_{index:02d}",
            )
        )
    return tuple(scenarios)


def minimum_activated_hazards_to_goal(scenario: UnavoidableScenario) -> int:
    """Return the minimum number of distinct trigger hazards on any path."""
    start_state = (scenario.start, frozenset())
    frontier: list[tuple[int, int, GridCell, frozenset[int]]] = [
        (0, 0, scenario.start, frozenset())
    ]
    best: dict[tuple[GridCell, frozenset[int]], int] = {start_state: 0}
    counter = 0
    while frontier:
        count, _, cell, active = heapq.heappop(frontier)
        state = (cell, active)
        if count != best.get(state):
            continue
        if cell == scenario.goal:
            return count
        for neighbor in scenario.grid.neighbors4(cell):
            additions = frozenset(
                index
                for index, closure in enumerate(scenario.model.closures)
                if closure.trigger == (cell, neighbor)
            )
            next_active = active | additions
            next_state = (neighbor, next_active)
            next_count = len(next_active)
            if next_count < best.get(next_state, 10**9):
                best[next_state] = next_count
                counter += 1
                heapq.heappush(
                    frontier,
                    (next_count, counter, neighbor, next_active),
                )
    raise RuntimeError("generated scenario has no start-to-goal path")


def _plan_scenario(
    scenario: UnavoidableScenario,
    *,
    recoverability_weight: float,
) -> dict[str, object]:
    fixed_hazard = _state_only_marginal_hazard(scenario.model)
    exact_capacity = max(16, len(scenario.model.closures))
    return {
        "shortest": commitment_aware_astar(
            scenario.grid,
            scenario.start,
            scenario.goal,
            safe_cells=scenario.safe,
            hazard_model=scenario.model,
            mode=CommitmentPlannerMode.SHORTEST,
        ),
        "state_only_single": hazard_reliability_astar(
            scenario.grid,
            scenario.start,
            scenario.goal,
            safe_cells=scenario.safe,
            hazard=fixed_hazard,
            mode=HazardReliabilityMode.SINGLE_RETURN,
            config=HazardReliabilityAStarConfig(
                reliability_weight=recoverability_weight
            ),
        ),
        "state_only_exact": hazard_reliability_astar(
            scenario.grid,
            scenario.start,
            scenario.goal,
            safe_cells=scenario.safe,
            hazard=fixed_hazard,
            mode=HazardReliabilityMode.EXACT_RETURN,
            config=HazardReliabilityAStarConfig(
                reliability_weight=recoverability_weight,
                max_hazard_cells=exact_capacity,
            ),
        ),
        "history_exact": commitment_aware_astar(
            scenario.grid,
            scenario.start,
            scenario.goal,
            safe_cells=scenario.safe,
            hazard_model=scenario.model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
            config=CommitmentAwareAStarConfig(
                recoverability_weight=recoverability_weight,
                max_hazard_cells=exact_capacity,
            ),
        ),
    }


def run_unavoidable_history_benchmark(
    *,
    scenarios: tuple[UnavoidableScenario, ...] | None = None,
    seeds: tuple[int, ...] = FROZEN_EXECUTION_SEEDS,
    recoverability_weight: float = 8.0,
) -> list[UnavoidableRecord]:
    """Run paired post-commitment closure realizations on the frozen suite."""
    if not seeds:
        raise ValueError("seeds cannot be empty")
    worlds = frozen_unavoidable_scenarios() if scenarios is None else scenarios
    if not worlds:
        raise ValueError("scenarios cannot be empty")

    records: list[UnavoidableRecord] = []
    for scenario in worlds:
        minimum = minimum_activated_hazards_to_goal(scenario)
        if minimum < scenario.module_count:
            raise RuntimeError(
                f"scenario {scenario.name} admits an unexpectedly low-trigger route: {minimum}"
            )
        plans = _plan_scenario(
            scenario,
            recoverability_weight=recoverability_weight,
        )
        for planner, result in plans.items():
            if not result.success:
                raise RuntimeError(f"planner {planner} failed in {scenario.name}")
            path = tuple(result.path)
            active = _activated_indices(scenario.model, path)
            final_exact = commitment_aware_astar(
                scenario.grid,
                scenario.goal,
                scenario.goal,
                safe_cells=scenario.safe,
                hazard_model=scenario.model,
                mode=CommitmentPlannerMode.SHORTEST,
                initial_activated_closures=frozenset(active),
            ).final_return_probability
            for seed in seeds:
                updated, realized = _realize_after_commitment(
                    scenario.grid,
                    scenario.goal,
                    scenario.model,
                    active,
                    seed,
                )
                failure = return_failure_probability(
                    updated,
                    scenario.goal,
                    scenario.safe,
                ) >= 1.0
                records.append(
                    UnavoidableRecord(
                        scenario=scenario.name,
                        seed=seed,
                        planner=planner,
                        path_length=result.geometric_length,
                        activated_closure_count=len(active),
                        realized_closure_count=realized,
                        final_exact_return_probability=final_exact,
                        return_infeasible=failure,
                    )
                )
    return records


def summarize_unavoidable_history(
    records: list[UnavoidableRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")
    result: dict[str, object] = {
        "generator_seed": FROZEN_GENERATOR_SEED,
        "scenario_count": len({row.scenario for row in records}),
    }
    for scenario in sorted({row.scenario for row in records}):
        rows = [row for row in records if row.scenario == scenario]
        planners = sorted({row.planner for row in rows})
        block: dict[str, object] = {}
        for planner in planners:
            planner_rows = [row for row in rows if row.planner == planner]
            block[planner] = {
                "trials": len(planner_rows),
                "path_length": planner_rows[0].path_length,
                "activated_closure_count": planner_rows[0].activated_closure_count,
                "final_exact_return_probability": planner_rows[0].final_exact_return_probability,
                "return_infeasible_rate": sum(row.return_infeasible for row in planner_rows)
                / len(planner_rows),
            }

        baseline = {
            row.seed: row
            for row in rows
            if row.planner == "shortest"
        }
        effects: dict[str, object] = {}
        for planner in planners:
            if planner == "shortest":
                continue
            candidate = {
                row.seed: row
                for row in rows
                if row.planner == planner
            }
            common = sorted(set(baseline) & set(candidate))
            if not common:
                continue
            effects[planner] = asdict(
                paired_binary_effect(
                    [baseline[seed].return_infeasible for seed in common],
                    [candidate[seed].return_infeasible for seed in common],
                    resamples=5000,
                    seed=4100 + sum(ord(ch) for ch in scenario + planner),
                )
            )
        block["paired_binary_effects_vs_shortest"] = effects
        result[scenario] = block
    return result


def write_unavoidable_history_artifacts(
    records: list[UnavoidableRecord],
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
            summarize_unavoidable_history(records),
            handle,
            indent=2,
            sort_keys=True,
        )
    protocol = {
        "generator_seed": FROZEN_GENERATOR_SEED,
        "scenario_count": FROZEN_SCENARIO_COUNT,
        "execution_seeds": len(FROZEN_EXECUTION_SEEDS),
        "probability_choices": PROBABILITY_CHOICES,
        "invariant": "every start-to-goal route activates at least one hazard per module",
    }
    with (target / "protocol.json").open("w", encoding="utf-8") as handle:
        json.dump(protocol, handle, indent=2, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results/unavoidable_history")
    parser.add_argument("--scenario-count", type=int, default=FROZEN_SCENARIO_COUNT)
    parser.add_argument("--seeds", type=int, default=len(FROZEN_EXECUTION_SEEDS))
    args = parser.parse_args()

    scenarios = frozen_unavoidable_scenarios(count=args.scenario_count)
    records = run_unavoidable_history_benchmark(
        scenarios=scenarios,
        seeds=tuple(range(args.seeds)),
    )
    write_unavoidable_history_artifacts(records, args.output_dir)


if __name__ == "__main__":
    main()
