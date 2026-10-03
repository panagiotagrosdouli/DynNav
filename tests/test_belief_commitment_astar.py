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
