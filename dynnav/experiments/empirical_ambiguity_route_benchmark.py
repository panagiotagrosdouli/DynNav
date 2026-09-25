"""Finite-data G1 benchmark for learned closure-dependence ambiguity."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.empirical_topology_ambiguity import (
    ClosureObservation,
    fit_empirical_topology_ambiguity,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridMap
from dynnav.planners.robust_commitment_astar import (
    RobustCommitmentAStarConfig,
    robust_commitment_astar,
)


@dataclass(frozen=True)
class EmpiricalAmbiguityRouteRecord:
    dependence: str
    training_size: int
    repetition: int
    method: str
    path_length: int
    activated_hazards: int
    modeled_final_return: float
    true_failure_probability: float
    shortcut_selected: bool


def _problem(
    p_first: float,
    p_second: float,
) -> tuple[GridMap, tuple[int, int], tuple[int, int], CommitmentHazardModel]:
    width, height = 5, 3
    free = {(x, 0) for x in range(width)}
    free.update({(x, 2) for x in range(width)})
    free.update({(0, 1), (4, 1)})
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(((2, 0), (3, 0)), (1, 0), p_first),
            CommitmentClosure(((3, 0), (4, 0)), (1, 2), p_second),
        )
    )
    return grid, (0, 0), (4, 0), model


def _draw_pair(rng: random.Random, dependence: str) -> tuple[bool, bool]:
    if dependence == "independent":
        return rng.random() < 0.5, rng.random() < 0.5
    if dependence == "common_cause":
        closed = rng.random() < 0.5
        return closed, closed
    if dependence == "anti_correlated":
        first = rng.random() < 0.5
        return first, not first
    raise ValueError(f"unknown dependence: {dependence}")


def _true_joint_failure_probability(dependence: str) -> float:
    if dependence == "independent":
        return 0.25
    if dependence == "common_cause":
        return 0.5
    if dependence == "anti_correlated":
        return 0.0
    raise ValueError(f"unknown dependence: {dependence}")


def run_empirical_ambiguity_route_benchmark(
    *,
    training_sizes: tuple[int, ...] = (20, 50, 100, 500),
    repetitions: int = 50,
    family_confidence: float = 0.95,
    seed: int = 20260925,
) -> list[EmpiricalAmbiguityRouteRecord]:
    """Measure route choice when dependence information is learned from data."""

    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if any(size <= 0 for size in training_sizes):
        raise ValueError("training sizes must be positive")

    records: list[EmpiricalAmbiguityRouteRecord] = []
    hazard_cells = ((1, 0), (1, 2))

    for condition_index, dependence in enumerate(
        ("independent", "common_cause", "anti_correlated")
    ):
        for size_index, training_size in enumerate(training_sizes):
            for repetition in range(repetitions):
                rng = random.Random(
                    seed
                    + 100_000 * condition_index
                    + 1_000 * size_index
                    + repetition
                )
                observations: list[ClosureObservation] = []
                for _ in range(training_size):
                    first, second = _draw_pair(rng, dependence)
                    closed = frozenset(
                        cell
                        for cell, value in zip(
                            hazard_cells,
                            (first, second),
                            strict=True,
                        )
                        if value
                    )
                    observations.append(ClosureObservation(closed))

                marginal_fit = fit_empirical_topology_ambiguity(
                    observations,
                    hazard_cells,
                    family_confidence=family_confidence,
                    include_pairwise=False,
                )
                pairwise_fit = fit_empirical_topology_ambiguity(
                    observations,
                    hazard_cells,
                    family_confidence=family_confidence,
                    include_pairwise=True,
                )

                p_first = marginal_fit.marginal_estimates[hazard_cells[0]]
                p_second = marginal_fit.marginal_estimates[hazard_cells[1]]
                grid, start, goal, model = _problem(p_first, p_second)

                plug_in = commitment_aware_astar(
                    grid,
                    start,
                    goal,
                    safe_cells={start},
                    hazard_model=model,
                    mode=CommitmentPlannerMode.HISTORY_AWARE,
                    config=CommitmentAwareAStarConfig(
                        recoverability_weight=12.0,
                    ),
                )
                robust_marginal = robust_commitment_astar(
                    grid,
                    start,
                    goal,
                    safe_cells={start},
                    hazard_model=model,
                    config=RobustCommitmentAStarConfig(
                        recoverability_weight=12.0,
                        marginal_intervals=marginal_fit.ambiguity.marginals,
                    ),
                )
                robust_pairwise = robust_commitment_astar(
                    grid,
                    start,
                    goal,
                    safe_cells={start},
                    hazard_model=model,
                    config=RobustCommitmentAStarConfig(
                        recoverability_weight=12.0,
                        marginal_intervals=pairwise_fit.ambiguity.marginals,
                        pairwise_constraints=pairwise_fit.ambiguity.pairwise,
                    ),
                )

                planner_rows = (
                    (
                        "plugin_independence",
                        plug_in.geometric_length,
                        plug_in.activated_closure_count,
                        plug_in.final_return_probability,
                    ),
                    (
                        "empirical_marginal_robust",
                        robust_marginal.geometric_length,
                        robust_marginal.activated_hazard_count,
                        robust_marginal.final_worst_case_return_probability,
                    ),
                    (
                        "empirical_pairwise_robust",
                        robust_pairwise.geometric_length,
                        robust_pairwise.activated_hazard_count,
                        robust_pairwise.final_worst_case_return_probability,
                    ),
                )
                true_joint_failure = _true_joint_failure_probability(dependence)
                for method, path_length, activated, modeled_return in planner_rows:
                    shortcut = activated == 2
                    records.append(
                        EmpiricalAmbiguityRouteRecord(
                            dependence=dependence,
                            training_size=training_size,
                            repetition=repetition,
                            method=method,
                            path_length=path_length,
                            activated_hazards=activated,
                            modeled_final_return=modeled_return,
                            true_failure_probability=(
                                true_joint_failure if shortcut else 0.0
                            ),
                            shortcut_selected=shortcut,
                        )
                    )

    return records
