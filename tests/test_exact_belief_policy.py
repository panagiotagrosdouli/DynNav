from __future__ import annotations

import pytest

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
from dynnav.planners.grid_map import GridMap


def test_exact_policy_solves_no_hazard_corridor() -> None:
    grid = GridMap.from_obstacles(3, 1)
    result = exact_finite_horizon_belief_policy(
        grid,
        (0, 0),
        (2, 0),
        safe_cells={(0, 0)},
        hazard_model=CommitmentHazardModel(()),
        arming_probabilities=(),
        detection_sensitivities=(),
        detection_specificities=(),
        config=ExactBeliefPolicyConfig(
            horizon=2,
            recoverability_weight=8.0,
        ),
    )

    assert result.success
    assert result.first_action == (1, 0)
    assert result.value == pytest.approx(2.0)
    assert result.states_evaluated > 0


def test_exact_policy_rejects_more_than_declared_tiny_hazard_limit() -> None:
    grid = GridMap.from_obstacles(5, 1)
    model = CommitmentHazardModel(
        tuple(
            CommitmentClosure(
                trigger=((index, 0), (index + 1, 0)),
                closure_cell=(index, 0),
                closure_probability=0.5,
            )
            for index in range(4)
        )
    )

    with pytest.raises(ValueError, match="limited to 3 hazards"):
        exact_finite_horizon_belief_policy(
            grid,
            (0, 0),
            (4, 0),
            safe_cells={(0, 0)},
            hazard_model=model,
            arming_probabilities=(0.5,) * 4,
            detection_sensitivities=(0.9,) * 4,
            detection_specificities=(0.9,) * 4,
        )


def test_exact_policy_and_receding_reference_agree_when_future_observation_has_no_value() -> None:
    grid = GridMap.from_obstacles(
        4,
        3,
        obstacles={(1, 0), (1, 2)},
    )
    current = (2, 1)
    goal = (3, 1)
    safe = {(0, 1)}
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=(current, goal),
                closure_cell=(1, 1),
                closure_probability=0.8,
            ),
        )
    )

    exact = exact_finite_horizon_belief_policy(
        grid,
        current,
        goal,
        safe_cells=safe,
        hazard_model=model,
        arming_probabilities=(1.0,),
        detection_sensitivities=(1.0,),
        detection_specificities=(1.0,),
        initial_belief=ActivationBelief.certain_inactive(),
        config=ExactBeliefPolicyConfig(
            horizon=3,
            recoverability_weight=4.0,
        ),
    )
    receding = belief_commitment_astar(
        grid,
        current,
        goal,
        safe_cells=safe,
        hazard_model=model,
        arming_probabilities=(1.0,),
        initial_belief=ActivationBelief.certain_inactive(),
        config=BeliefCommitmentAStarConfig(
            recoverability_weight=4.0,
        ),
    )

    assert exact.success
    assert receding.success
    assert exact.first_action == receding.path[1]
    assert exact.first_action in {(2, 0), (2, 2)}
    assert exact.value == pytest.approx(3.0)


def test_exact_policy_reports_failure_when_horizon_cannot_reach_goal() -> None:
    grid = GridMap.from_obstacles(4, 1)

    result = exact_finite_horizon_belief_policy(
        grid,
        (0, 0),
        (3, 0),
        safe_cells={(0, 0)},
        hazard_model=CommitmentHazardModel(()),
        arming_probabilities=(),
        detection_sensitivities=(),
        detection_specificities=(),
        config=ExactBeliefPolicyConfig(horizon=2),
    )

    assert not result.success
    assert result.first_action == (1, 0)
    assert result.value >= 1_000_000.0



def test_exact_policy_can_value_future_information_that_receding_search_ignores() -> None:
    width, height = 9, 6
    start = (0, 3)
    junction = (4, 3)
    current = (6, 3)
    goal = (7, 3)

    free = {start, junction, current, goal, (5, 3)}
    free.update((x, 2) for x in range(5))
    free.update((x, 5) for x in range(5))
    free.update({(0, 4), (4, 4)})
    # A long post-junction detour from current to goal that avoids hazard 1.
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

    exact = exact_finite_horizon_belief_policy(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.3, 1.0),
        detection_sensitivities=(1.0, 1.0),
        detection_specificities=(1.0, 1.0),
        config=ExactBeliefPolicyConfig(
            horizon=16,
            recoverability_weight=16.0,
        ),
    )
    receding = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.3, 1.0),
        config=BeliefCommitmentAStarConfig(
            recoverability_weight=16.0,
        ),
    )

    assert exact.success
    assert receding.success
    assert exact.first_action == (0, 2)
    assert receding.path[1] == (0, 4)

    action_values = dict(exact.action_values)
    assert action_values[receding.path[1]] > exact.value
