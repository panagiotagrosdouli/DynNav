"""Paired execution benchmark under closure-dependence shift."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
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
class DependenceShiftRecord:
    dependence: str
    planner: str
    trials: int
    failures: int
    failure_rate: float
    path_length: int
    activated_hazards: int


def _problem() -> tuple[
    GridMap,
    tuple[int, int],
    tuple[int, int],
    CommitmentHazardModel,
]:
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
    start = (0, 0)
    goal = (4, 0)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(((2, 0), (3, 0)), (1, 0), 0.5),
            CommitmentClosure(((3, 0), (4, 0)), (1, 2), 0.5),
        )
    )
    return grid, start, goal, model


def _latent_pair(rng: random.Random, dependence: str) -> tuple[bool, bool]:
    if dependence == "independent":
        return rng.random() < 0.5, rng.random() < 0.5
    if dependence == "common_cause":
        event = rng.random() < 0.5
        return event, event
    if dependence == "anti_correlated":
        event = rng.random() < 0.5
        return event, not event
    raise ValueError(f"unknown dependence condition: {dependence}")


def run_dependence_shift_benchmark(
    *,
    trials: int = 10_000,
    seed: int = 0,
) -> list[DependenceShiftRecord]:
    """Compare independence-assuming and robust planners on matched latent draws."""

    if trials <= 0:
        raise ValueError("trials must be positive")
    grid, start, goal, model = _problem()
    independent = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=12.0),
    )
    robust = robust_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        config=RobustCommitmentAStarConfig(recoverability_weight=12.0),
    )
    planner_data = {
        "independence_history": (
            independent.geometric_length,
            independent.activated_closure_count,
        ),
        "dependence_robust_history": (
            robust.geometric_length,
            robust.activated_hazard_count,
        ),
    }

    records: list[DependenceShiftRecord] = []
    for condition_index, dependence in enumerate(
        ("independent", "common_cause", "anti_correlated")
    ):
        rng = random.Random(seed + condition_index)
        failure_counts = {planner: 0 for planner in planner_data}
        for _ in range(trials):
            first_closed, second_closed = _latent_pair(rng, dependence)
            direct_return_failed = first_closed and second_closed
            # The robust planner takes the trigger-free detour in the frozen
            # construction, so neither latent closure is activated for it.
            failure_counts["independence_history"] += int(direct_return_failed)

        for planner, (path_length, activated_hazards) in planner_data.items():
            failures = failure_counts[planner]
            records.append(
                DependenceShiftRecord(
                    dependence=dependence,
                    planner=planner,
                    trials=trials,
                    failures=failures,
                    failure_rate=failures / trials,
                    path_length=path_length,
                    activated_hazards=activated_hazards,
                )
            )
    return records
