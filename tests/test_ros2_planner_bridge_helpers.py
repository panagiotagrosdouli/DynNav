import pytest

from dynnav.commitment_hazard import CommitmentHazardModel
from ros2_ws.src.dynnav_nav2.dynnav_nav2.dynnav_planner_bridge import (
    ExecutionHistory,
    PlannerBridgeConfig,
    advance_execution_history,
    format_path,
    parse_cells,
    parse_commitment_hazards,
    parse_transition,
    plan_grid_path,
    plan_history_conditioned_grid_path,
)


def test_parse_cells_parses_comma_separated_grid_cells():
    assert parse_cells("1:2,3:4") == ((1, 2), (3, 4))


def test_parse_transition_preserves_direction():
    assert parse_transition("1:2>2:2") == ((1, 2), (2, 2))


def test_parse_commitment_hazards_reads_trigger_closure_and_probability():
    hazards = parse_commitment_hazards("1:1>2:1@0:1@0.8;2:1>3:1@1:1@0.4")

    assert len(hazards) == 2
    assert hazards[0].trigger == ((1, 1), (2, 1))
    assert hazards[0].closure_cell == (0, 1)
    assert hazards[0].closure_probability == pytest.approx(0.8)


def test_format_path_uses_arrow_notation():
    assert format_path([(0, 0), (1, 0), (1, 1)]) == "(0,0) -> (1,0) -> (1,1)"


def test_plan_grid_path_returns_path_for_simple_config():
    config = PlannerBridgeConfig(
        width=4,
        height=4,
        start=(0, 0),
        goal=(3, 0),
        obstacles=(),
    )

    path = plan_grid_path(config)

    assert path[0] == (0, 0)
    assert path[-1] == (3, 0)


def test_execution_history_activates_matching_hazard_and_advances_cell():
    hazards = parse_commitment_hazards("1:1>2:1@0:1@0.8")
    model = CommitmentHazardModel(hazards)
    history = advance_execution_history(
        ExecutionHistory((1, 1)),
        ((1, 1), (2, 1)),
        model,
    )

    assert history.current_cell == (2, 1)
    assert history.activated_hazards == frozenset({0})


def test_execution_history_rejects_out_of_order_transition():
    model = CommitmentHazardModel(())
    with pytest.raises(ValueError, match="does not match current cell"):
        advance_execution_history(
            ExecutionHistory((1, 1)),
            ((2, 1), (3, 1)),
            model,
        )


def test_history_conditioned_bridge_preserves_previously_activated_hazard():
    hazards = parse_commitment_hazards("1:1>2:1@0:1@0.8")
    config = PlannerBridgeConfig(
        width=5,
        height=3,
        start=(0, 1),
        goal=(4, 1),
        obstacles=(),
        planner_mode="history_aware",
        safe_cells=((0, 1),),
        commitment_hazards=hazards,
        recoverability_weight=4.0,
    )

    path, minimum_return, active_count = plan_history_conditioned_grid_path(
        config,
        ExecutionHistory((2, 1), frozenset({0})),
    )

    assert path[0] == (2, 1)
    assert path[-1] == (4, 1)
    assert active_count == 1
    assert minimum_return == pytest.approx(0.2)
