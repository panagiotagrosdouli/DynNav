"""Constructed V4 counterexample for future observation-contingent value.

The world is designed so a shorter outbound route executes a trigger whose
latent arming state is observed perfectly. If the hazard arms, the exact policy
can later choose a long final detour; if it does not arm, it takes a short final
edge. The receding predictive-belief A* does not price that future contingent
choice in its initial search and selects a longer trigger-free outbound route.

This is a development approximation-boundary case, not held-out evidence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.activation_belief import ActivationBelief
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.belief_commitment_astar import (
    BeliefCommitmentAStarConfig,
    belief_commitment_astar,
)
from dynnav.planners.exact_belief_policy import (
    ExactBeliefPolicyConfig,
    exact_finite_horizon_belief_policy,
)
from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class InformationValueCounterexample:
    exact_first_action: GridCell | None
    receding_first_action: GridCell | None
    exact_value: float
    receding_first_action_exact_value: float
    first_action_regret: float
    exact_action_values: tuple[tuple[GridCell, float], ...]
    exact_states_evaluated: int
    receding_path: tuple[GridCell, ...]
    receding_cost: float


def information_value_world() -> tuple[
    GridMap,
    GridCell,
    GridCell,
    set[GridCell],
    CommitmentHazardModel,
]:
    width, height = 9, 6
    start = (0, 3)
    junction = (4, 3)
    current = (6, 3)
    goal = (7, 3)

    free = {start, junction, current, goal, (5, 3)}
    free.update((x, 2) for x in range(5))
    free.update((x, 5) for x in range(5))
    free.update({(0, 4), (4, 4)})
    free.update({(6, 2), (6, 1), (7, 1), (8, 1), (8, 2), (8, 3)})
    obstacles = {
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 2), (3, 2)),
                closure_cell=(2, 2),
                closure_probability=0.8,
            ),
            CommitmentClosure(
                trigger=(current, goal),
                closure_cell=(2, 5),
                closure_probability=0.8,
            ),
        )
    )
    return grid, start, goal, {start}, model


def run_information_value_counterexample() -> InformationValueCounterexample:
    grid, start, goal, safe, model = information_value_world()

    exact = exact_finite_horizon_belief_policy(
        grid,
        start,
        goal,
        safe_cells=safe,
        hazard_model=model,
        arming_probabilities=(0.3, 1.0),
        detection_sensitivities=(1.0, 1.0),
        detection_specificities=(1.0, 1.0),
        initial_belief=ActivationBelief.certain_inactive(),
        config=ExactBeliefPolicyConfig(
            horizon=16,
            recoverability_weight=16.0,
        ),
    )
    receding = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells=safe,
        hazard_model=model,
        arming_probabilities=(0.3, 1.0),
        initial_belief=ActivationBelief.certain_inactive(),
        config=BeliefCommitmentAStarConfig(
            recoverability_weight=16.0,
        ),
    )
    receding_action = (
        receding.path[1]
        if receding.success and len(receding.path) >= 2
        else None
    )
    action_values = dict(exact.action_values)
    receding_value = action_values.get(receding_action, float("inf"))
    regret = receding_value - exact.value

    return InformationValueCounterexample(
        exact_first_action=exact.first_action,
        receding_first_action=receding_action,
        exact_value=exact.value,
        receding_first_action_exact_value=receding_value,
        first_action_regret=regret,
        exact_action_values=exact.action_values,
        exact_states_evaluated=exact.states_evaluated,
        receding_path=receding.path,
        receding_cost=receding.cost,
    )


def write_information_value_counterexample(
    output_path: str | Path,
) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "development_only_not_publication_evidence",
        **asdict(run_information_value_counterexample()),
    }
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
