"""Predeclared G1 V2 topology x dependence held-out benchmark.

Protocol timestamp: GitHub issue #188 and its parameter addenda precede this
implementation. The benchmark intentionally includes topology/dependence
regimes where dependence helps, harms, or leaves a planner tied.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.robust_commitment_astar import (
    RobustCommitmentAStarConfig,
    robust_commitment_astar,
)
from dynnav.planners.scenario_commitment_astar import (
    JointDependenceMode,
    ScenarioCommitmentAStarConfig,
    scenario_belief_for_active,
    scenario_commitment_astar,
)
from dynnav.recoverability import return_failure_probability
from dynnav.recoverability_scenarios import exact_scenario_safe_return_probability


@dataclass(frozen=True)
class DependenceHeldoutScenario:
    name: str
    grid: GridMap
    start: GridCell
    goal: GridCell
    safe: set[GridCell]
    model: CommitmentHazardModel
    dependence_modes: tuple[JointDependenceMode, ...]


@dataclass(frozen=True)
class DependenceHeldoutRecord:
    scenario: str
    dependence: str
    recoverability_weight: float
    planner: str
    repetition: int
    seed: int
    trials: int
    path_length: int
    activated_hazard_count: int
    predicted_return_probability: float
    true_joint_return_probability: float
    failures: int
    failure_rate: float
    safe_at_0_50: bool
    safe_at_0_70: bool
    safe_at_0_90: bool
    false_safe_rate_at_0_50: float
    false_safe_rate_at_0_70: float
    false_safe_rate_at_0_90: float
    nodes_expanded: int
    planning_time_ms: float


def _grid_from_free(
    width: int,
    height: int,
    free: set[GridCell],
) -> GridMap:
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    return GridMap.from_obstacles(width, height, obstacles=obstacles)


def frozen_g1_v2_scenarios() -> tuple[DependenceHeldoutScenario, ...]:
    """Return the four source-frozen V2 topology families."""

    # Parallel redundant return: direct central mission route activates one
    # future closure on each of three alternative return corridors. A longer
    # top-row mission route avoids all three trigger transitions.
    parallel_free = {
        (x, y)
        for y in (0, 2, 4)
        for x in range(7)
    }
    parallel_free.update({(0, y) for y in range(5)})
    parallel_free.update({(6, y) for y in range(5)})
    parallel = DependenceHeldoutScenario(
        name="parallel_three_return",
        grid=_grid_from_free(7, 5, parallel_free),
        start=(0, 2),
        goal=(6, 2),
        safe={(0, 2)},
        model=CommitmentHazardModel(
            (
                CommitmentClosure(((3, 2), (4, 2)), (2, 0), 0.5),
                CommitmentClosure(((4, 2), (5, 2)), (2, 2), 0.5),
                CommitmentClosure(((5, 2), (6, 2)), (2, 4), 0.5),
            )
        ),
        dependence_modes=(
            JointDependenceMode.INDEPENDENT,
            JointDependenceMode.COMMON_CAUSE,
            JointDependenceMode.PARTIAL_MIXTURE,
        ),
    )

    # Serial cuts: both future closure cells lie on the shared prefix that every
    # return route must cross. Common-cause dependence is a mandatory
    # sign-reversal control because it makes "neither closes" more likely than
    # independence at fixed p=0.5 marginals.
    serial_free = {(x, 1) for x in range(7)}
    serial_free.update({(x, 0) for x in range(3, 7)})
    serial = DependenceHeldoutScenario(
        name="serial_two_cut",
        grid=_grid_from_free(7, 3, serial_free),
        start=(0, 1),
        goal=(6, 1),
        safe={(0, 1)},
        model=CommitmentHazardModel(
            (
                CommitmentClosure(((4, 1), (5, 1)), (1, 1), 0.5),
                CommitmentClosure(((5, 1), (6, 1)), (2, 1), 0.5),
            )
        ),
        dependence_modes=(
            JointDependenceMode.INDEPENDENT,
            JointDependenceMode.COMMON_CAUSE,
            JointDependenceMode.ANTI_CORRELATED,
            JointDependenceMode.PARTIAL_MIXTURE,
        ),
    )

    # Hybrid: one shared serial cut plus two alternative branch cuts. The short
    # upper mission branch activates all three hazards; a longer lower branch
    # avoids the trigger transitions.
    hybrid_free = {(x, 1) for x in range(3)}
    hybrid_free.update({(x, 0) for x in range(2, 6)})
    hybrid_free.update({(x, 3) for x in range(2, 6)})
    hybrid_free.update({(2, 2), (5, 1), (5, 2), (6, 1)})
    hybrid = DependenceHeldoutScenario(
        name="hybrid_shared_plus_parallel",
        grid=_grid_from_free(7, 4, hybrid_free),
        start=(0, 1),
        goal=(6, 1),
        safe={(0, 1)},
        model=CommitmentHazardModel(
            (
                CommitmentClosure(((2, 1), (2, 0)), (1, 1), 0.5),
                CommitmentClosure(((3, 0), (4, 0)), (3, 0), 0.5),
                CommitmentClosure(((5, 0), (5, 1)), (3, 3), 0.5),
            )
        ),
        dependence_modes=(
            JointDependenceMode.INDEPENDENT,
            JointDependenceMode.COMMON_CAUSE,
            JointDependenceMode.PARTIAL_MIXTURE,
        ),
    )

    # Action-selection fork: the short upper route activates two serial cuts;
    # the longer lower route activates two hazards on alternative return
    # branches. Thus the route ordering itself can depend on the true joint law.
    fork_free = {(x, 1) for x in range(3)}
    fork_free.update({(x, 0) for x in range(2, 6)})
    fork_free.update({(x, 3) for x in range(2, 6)})
    fork_free.update({(2, 2), (5, 1), (5, 2), (6, 1)})
    fork = DependenceHeldoutScenario(
        name="fork_serial_vs_parallel",
        grid=_grid_from_free(7, 4, fork_free),
        start=(0, 1),
        goal=(6, 1),
        safe={(0, 1)},
        model=CommitmentHazardModel(
            (
                CommitmentClosure(((2, 1), (2, 0)), (1, 1), 0.5),
                CommitmentClosure(((3, 0), (4, 0)), (2, 1), 0.5),
                CommitmentClosure(((2, 2), (2, 3)), (3, 0), 0.5),
                CommitmentClosure(((3, 3), (4, 3)), (3, 3), 0.5),
            )
        ),
        dependence_modes=(
            JointDependenceMode.INDEPENDENT,
            JointDependenceMode.COMMON_CAUSE,
            JointDependenceMode.PARTIAL_MIXTURE,
        ),
    )

    return parallel, serial, hybrid, fork


def _activated_indices(
    model: CommitmentHazardModel,
    path: tuple[GridCell, ...] | list[GridCell],
) -> frozenset[int]:
    transitions = set(zip(path, path[1:], strict=False))
    return frozenset(
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger in transitions
    )


def _latent_closed_indices(
    rng: random.Random,
    hazard_count: int,
    dependence: JointDependenceMode,
) -> frozenset[int]:
    if dependence is JointDependenceMode.INDEPENDENT:
        return frozenset(
            index
            for index in range(hazard_count)
            if rng.random() < 0.5
        )
    if dependence is JointDependenceMode.COMMON_CAUSE:
        return (
            frozenset(range(hazard_count))
            if rng.random() < 0.5
            else frozenset()
        )
    if dependence is JointDependenceMode.PARTIAL_MIXTURE:
        if rng.random() < 0.5:
            return (
                frozenset(range(hazard_count))
                if rng.random() < 0.5
                else frozenset()
            )
        return frozenset(
            index
            for index in range(hazard_count)
            if rng.random() < 0.5
        )
    if dependence is JointDependenceMode.ANTI_CORRELATED:
        if hazard_count != 2:
            raise ValueError(
                "global anti-correlated V2 latent law requires exactly two hazards"
            )
        return frozenset({0 if rng.random() < 0.5 else 1})
    raise ValueError(f"unsupported dependence: {dependence}")


def _realized_grid(
    scenario: DependenceHeldoutScenario,
    active: frozenset[int],
    latent_closed: frozenset[int],
) -> GridMap:
    obstacles = set(scenario.grid.obstacles)
    for index in active & latent_closed:
        closure_cell = scenario.model.closures[index].closure_cell
        if closure_cell != scenario.goal:
            obstacles.add(closure_cell)
    return GridMap.from_obstacles(
        scenario.grid.width,
        scenario.grid.height,
        obstacles=obstacles,
        risk=scenario.grid.risk,
        uncertainty=scenario.grid.uncertainty,
    )


def _true_return_probability(
    scenario: DependenceHeldoutScenario,
    active: frozenset[int],
    dependence: JointDependenceMode,
) -> float:
    belief = scenario_belief_for_active(
        scenario.model,
        active,
        dependence,
        common_cause_mixture_weight=0.5,
    )
    return exact_scenario_safe_return_probability(
        scenario.grid,
        scenario.goal,
        scenario.safe,
        belief,
    )


def _plan_set(
    scenario: DependenceHeldoutScenario,
    dependence: JointDependenceMode,
    weight: float,
) -> dict[str, object]:
    shortest = commitment_aware_astar(
        scenario.grid,
        scenario.start,
        scenario.goal,
        safe_cells=scenario.safe,
        hazard_model=scenario.model,
        mode=CommitmentPlannerMode.SHORTEST,
    )
    independence = commitment_aware_astar(
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
    )
    robust = robust_commitment_astar(
        scenario.grid,
        scenario.start,
        scenario.goal,
        safe_cells=scenario.safe,
        hazard_model=scenario.model,
        config=RobustCommitmentAStarConfig(
            recoverability_weight=weight,
            max_hazard_cells=12,
        ),
    )
    oracle = scenario_commitment_astar(
        scenario.grid,
        scenario.start,
        scenario.goal,
        safe_cells=scenario.safe,
        hazard_model=scenario.model,
        dependence=dependence,
        config=ScenarioCommitmentAStarConfig(
            recoverability_weight=weight,
            common_cause_mixture_weight=0.5,
        ),
    )
    results = {
        "shortest": shortest,
        "independence_history": independence,
        "dependence_robust_history": robust,
        "true_joint_oracle": oracle,
    }
    if any(not getattr(result, "success") for result in results.values()):
        raise RuntimeError(
            f"planner failure in {scenario.name}/{dependence.value}/lambda={weight}"
        )
    return results


def _predicted_return(planner: str, result: object) -> float:
    if planner == "dependence_robust_history":
        return float(getattr(result, "final_worst_case_return_probability"))
    return float(getattr(result, "final_return_probability"))


def _activated_count(planner: str, result: object) -> int:
    if planner == "dependence_robust_history":
        return int(getattr(result, "activated_hazard_count"))
    if planner == "true_joint_oracle":
        return int(getattr(result, "activated_hazard_count"))
    return int(getattr(result, "activated_closure_count"))


def run_g1_v2_heldout_benchmark(
    *,
    weights: tuple[float, ...] = (0.0, 2.0, 4.0, 8.0, 12.0),
    trials_per_condition: int = 2_000,
    repetitions: int = 5,
    seed: int = 20260925,
) -> list[DependenceHeldoutRecord]:
    """Run the predeclared topology x dependence x lambda frontier."""

    if trials_per_condition <= 0:
        raise ValueError("trials_per_condition must be positive")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if not weights or any(weight < 0.0 for weight in weights):
        raise ValueError("weights must be a non-empty tuple of non-negative values")

    records: list[DependenceHeldoutRecord] = []
    condition_index = 0
    for scenario in frozen_g1_v2_scenarios():
        scenario.model.validate(scenario.grid)
        for dependence in scenario.dependence_modes:
            for weight in weights:
                plans = _plan_set(scenario, dependence, weight)
                plan_metadata: dict[str, tuple[frozenset[int], float]] = {}
                for planner, result in plans.items():
                    path = tuple(getattr(result, "path"))
                    active = _activated_indices(scenario.model, path)
                    true_return = _true_return_probability(
                        scenario,
                        active,
                        dependence,
                    )
                    plan_metadata[planner] = (active, true_return)

                for repetition in range(repetitions):
                    condition_seed = (
                        seed
                        + condition_index * 100_003
                        + int(round(weight * 1000.0)) * 17
                        + repetition
                    )
                    rng = random.Random(condition_seed)
                    failure_counts = {planner: 0 for planner in plans}
                    failure_cache: dict[
                        tuple[str, frozenset[int]],
                        bool,
                    ] = {}

                    for _ in range(trials_per_condition):
                        latent_closed = _latent_closed_indices(
                            rng,
                            len(scenario.model.closures),
                            dependence,
                        )
                        for planner, (active, _) in plan_metadata.items():
                            cache_key = (planner, latent_closed)
                            failure = failure_cache.get(cache_key)
                            if failure is None:
                                realized = _realized_grid(
                                    scenario,
                                    active,
                                    latent_closed,
                                )
                                failure = return_failure_probability(
                                    realized,
                                    scenario.goal,
                                    scenario.safe,
                                ) >= 1.0
                                failure_cache[cache_key] = failure
                            failure_counts[planner] += int(failure)

                    for planner, result in plans.items():
                        active, true_return = plan_metadata[planner]
                        predicted = _predicted_return(planner, result)
                        failures = failure_counts[planner]
                        failure_rate = failures / trials_per_condition
                        safe_050 = predicted >= 0.50
                        safe_070 = predicted >= 0.70
                        safe_090 = predicted >= 0.90
                        records.append(
                            DependenceHeldoutRecord(
                                scenario=scenario.name,
                                dependence=dependence.value,
                                recoverability_weight=weight,
                                planner=planner,
                                repetition=repetition,
                                seed=condition_seed,
                                trials=trials_per_condition,
                                path_length=int(
                                    getattr(result, "geometric_length")
                                ),
                                activated_hazard_count=len(active),
                                predicted_return_probability=predicted,
                                true_joint_return_probability=true_return,
                                failures=failures,
                                failure_rate=failure_rate,
                                safe_at_0_50=safe_050,
                                safe_at_0_70=safe_070,
                                safe_at_0_90=safe_090,
                                false_safe_rate_at_0_50=(
                                    failure_rate if safe_050 else 0.0
                                ),
                                false_safe_rate_at_0_70=(
                                    failure_rate if safe_070 else 0.0
                                ),
                                false_safe_rate_at_0_90=(
                                    failure_rate if safe_090 else 0.0
                                ),
                                nodes_expanded=int(
                                    getattr(result, "nodes_expanded")
                                ),
                                planning_time_ms=float(
                                    getattr(result, "planning_time_ms")
                                ),
                            )
                        )
                condition_index += 1
    return records



def summarize_g1_v2_heldout(
    records: list[DependenceHeldoutRecord],
) -> list[dict[str, object]]:
    """Aggregate repetitions without selecting a post-hoc preferred weight."""

    if not records:
        raise ValueError("records cannot be empty")
    groups: dict[
        tuple[str, str, float, str],
        list[DependenceHeldoutRecord],
    ] = {}
    for record in records:
        key = (
            record.scenario,
            record.dependence,
            record.recoverability_weight,
            record.planner,
        )
        groups.setdefault(key, []).append(record)

    summary: list[dict[str, object]] = []
    for key, members in sorted(groups.items(), key=lambda item: str(item[0])):
        scenario, dependence, weight, planner = key
        total_trials = sum(row.trials for row in members)
        total_failures = sum(row.failures for row in members)
        predicted_values = {row.predicted_return_probability for row in members}
        true_values = {row.true_joint_return_probability for row in members}
        path_lengths = {row.path_length for row in members}
        active_counts = {row.activated_hazard_count for row in members}
        if (
            len(predicted_values) != 1
            or len(true_values) != 1
            or len(path_lengths) != 1
            or len(active_counts) != 1
        ):
            raise ValueError("deterministic plan metadata changed across repetitions")

        predicted = next(iter(predicted_values))
        true_return = next(iter(true_values))
        failure_rate = total_failures / total_trials
        summary.append(
            {
                "scenario": scenario,
                "dependence": dependence,
                "recoverability_weight": weight,
                "planner": planner,
                "repetitions": len(members),
                "total_trials": total_trials,
                "path_length": next(iter(path_lengths)),
                "activated_hazard_count": next(iter(active_counts)),
                "predicted_return_probability": predicted,
                "true_joint_return_probability": true_return,
                "return_prediction_error": predicted - true_return,
                "failures": total_failures,
                "failure_rate": failure_rate,
                "safe_at_0_50": predicted >= 0.50,
                "safe_at_0_70": predicted >= 0.70,
                "safe_at_0_90": predicted >= 0.90,
                "false_safe_rate_at_0_50": (
                    failure_rate if predicted >= 0.50 else 0.0
                ),
                "false_safe_rate_at_0_70": (
                    failure_rate if predicted >= 0.70 else 0.0
                ),
                "false_safe_rate_at_0_90": (
                    failure_rate if predicted >= 0.90 else 0.0
                ),
                "mean_nodes_expanded": (
                    sum(row.nodes_expanded for row in members) / len(members)
                ),
                "mean_planning_time_ms": (
                    sum(row.planning_time_ms for row in members) / len(members)
                ),
            }
        )
    return summary


def write_g1_v2_heldout_artifacts(
    records: list[DependenceHeldoutRecord],
    output_dir: str,
) -> None:
    """Write retained aggregate rows, summary, and run metadata."""

    import csv
    import json
    from dataclasses import asdict
    from pathlib import Path

    if not records:
        raise ValueError("records cannot be empty")
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    raw_rows = [asdict(record) for record in records]
    with (target / "records.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(raw_rows[0]))
        writer.writeheader()
        writer.writerows(raw_rows)

    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_g1_v2_heldout(records),
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    metadata = {
        "protocol_issue": 188,
        "scope": "G1 V2 synthetic topology x dependence heldout",
        "weights": sorted({row.recoverability_weight for row in records}),
        "thresholds": [0.50, 0.70, 0.90],
        "repetitions": len({row.repetition for row in records}),
        "trials_per_record": records[0].trials,
        "scenarios": sorted({row.scenario for row in records}),
        "dependence_modes": sorted({row.dependence for row in records}),
        "planners": sorted({row.planner for row in records}),
    }
    with (target / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
