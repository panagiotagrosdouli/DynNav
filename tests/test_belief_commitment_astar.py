from __future__ import annotations

import pytest

from dynnav.activation_belief import ActivationBelief
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.belief_commitment_astar import (
    BeliefCommitmentAStarConfig,
    belief_commitment_astar,
)
from dynnav.planners.grid_map import GridMap


def _trap_problem():
    grid = GridMap.from_obstacles(4, 3, obstacles={(1, 0), (1, 2)})
    start = (0, 1)
    goal = (3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((2, 1), (3, 1)),
                closure_cell=(1, 1),
                closure_probability=0.8,
            ),
        )
    )
    return grid, start, goal, model


def test_zero_arming_probability_collapses_to_shortest_geometric_route() -> None:
    grid, start, goal, model = _trap_problem()

    result = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.0,),
    )

    assert result.success
    assert result.geometric_length == 3
    assert result.final_predicted_return_probability == pytest.approx(1.0)
    assert result.final_expected_armed_hazards == pytest.approx(0.0)


def test_certain_arming_recovers_known_history_detour() -> None:
    grid, start, goal, model = _trap_problem()

    result = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(1.0,),
        config=BeliefCommitmentAStarConfig(recoverability_weight=4.0),
    )

    assert result.success
    assert result.geometric_length == 5
    assert result.final_predicted_return_probability == pytest.approx(1.0)
    assert result.final_expected_armed_hazards == pytest.approx(0.0)


def test_intermediate_arming_probability_can_change_route_at_fixed_weight() -> None:
    grid, start, goal, model = _trap_problem()

    low = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.2,),
        config=BeliefCommitmentAStarConfig(recoverability_weight=8.0),
    )
    medium = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.5,),
        config=BeliefCommitmentAStarConfig(recoverability_weight=8.0),
    )

    assert low.geometric_length == 3
    assert low.final_predicted_return_probability == pytest.approx(0.84)
    assert medium.geometric_length == 5
    assert medium.final_predicted_return_probability == pytest.approx(1.0)


def test_initial_posterior_is_used_in_planning() -> None:
    grid, start, goal, model = _trap_problem()
    posterior = ActivationBelief(
        {
            frozenset(): 0.75,
            frozenset({0}): 0.25,
        }
    )

    result = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.0,),
        initial_belief=posterior,
        config=BeliefCommitmentAStarConfig(recoverability_weight=8.0),
    )

    assert result.success
    assert result.final_belief_support_size == 2
    assert result.final_expected_armed_hazards == pytest.approx(0.25)


def test_arming_probability_vector_must_match_hazard_model() -> None:
    grid, start, goal, model = _trap_problem()

    with pytest.raises(ValueError, match="one value per commitment hazard"):
        belief_commitment_astar(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            arming_probabilities=(),
        )



def test_noisy_arming_observation_can_change_route_at_same_geometric_state() -> None:
    obstacles = {(2, 0), (2, 2), (2, 4)}
    grid = GridMap.from_obstacles(5, 5, obstacles=obstacles)
    current = (3, 2)
    goal = (4, 2)
    safe = {(0, 2)}
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((0, 2), (0, 1)),
                closure_cell=(2, 1),
                closure_probability=0.8,
            ),
            CommitmentClosure(
                trigger=(current, goal),
                closure_cell=(2, 3),
                closure_probability=0.8,
            ),
        )
    )

    predictive = ActivationBelief.certain_inactive().predict_after_trigger_execution(
        0,
        arming_probability=0.5,
    )
    armed_report = predictive.condition_on_arming_observation(
        0,
        observed_armed=True,
        detection_sensitivity=0.9,
        detection_specificity=0.9,
    )
    inactive_report = predictive.condition_on_arming_observation(
        0,
        observed_armed=False,
        detection_sensitivity=0.9,
        detection_specificity=0.9,
    )

    risky_belief = belief_commitment_astar(
        grid,
        current,
        goal,
        safe_cells=safe,
        hazard_model=model,
        arming_probabilities=(0.0, 1.0),
        initial_belief=armed_report,
        config=BeliefCommitmentAStarConfig(recoverability_weight=8.0),
    )
    reassuring_belief = belief_commitment_astar(
        grid,
        current,
        goal,
        safe_cells=safe,
        hazard_model=model,
        arming_probabilities=(0.0, 1.0),
        initial_belief=inactive_report,
        config=BeliefCommitmentAStarConfig(recoverability_weight=8.0),
    )

    assert armed_report.probability_armed(0) == pytest.approx(0.9)
    assert inactive_report.probability_armed(0) == pytest.approx(0.1)
    assert risky_belief.geometric_length == 3
    assert reassuring_belief.geometric_length == 1



def test_hard_return_threshold_uses_same_belief_but_changes_admissibility() -> None:
    grid, start, goal, model = _trap_problem()

    soft = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.2,),
        config=BeliefCommitmentAStarConfig(recoverability_weight=0.0),
    )
    hard = belief_commitment_astar(
        grid,
        start,
        goal,
        safe_cells={start},
        hazard_model=model,
        arming_probabilities=(0.2,),
        config=BeliefCommitmentAStarConfig(
            recoverability_weight=0.0,
            minimum_return_probability=0.9,
        ),
    )

    assert soft.geometric_length == 3
    assert soft.final_predicted_return_probability == pytest.approx(0.84)
    assert hard.geometric_length == 5
    assert hard.final_predicted_return_probability == pytest.approx(1.0)
