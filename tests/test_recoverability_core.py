import pytest

import dynnav.planners.recoverability_astar as recoverability_astar_module
from dynnav.planners.grid_map import GridMap
from dynnav.planners.recoverability_astar import (
    PlannerMode,
    RecoverabilityAStarConfig,
    recoverability_astar,
)
from dynnav.recoverability import analyze_recoverability, escape_option_count


def test_dead_end_has_one_escape_branch_and_high_irreversibility():
    obstacles = {
        (0, 0),
        (0, 2),
        (1, 0),
        (1, 2),
        (2, 0),
        (2, 2),
        (3, 0),
        (3, 2),
        (4, 0),
        (4, 1),
        (4, 2),
    }
    grid = GridMap.from_obstacles(5, 3, obstacles)

    assert escape_option_count(grid, (3, 1)) == 1
    state = analyze_recoverability(grid, (3, 1), {(0, 1)})
    assert state.bottleneck_exposure == 1.0
    assert 0.0 <= state.irreversibility <= 1.0


def test_open_junction_has_more_escape_options_than_dead_end():
    open_grid = GridMap.from_obstacles(5, 5)
    dead_end_grid = GridMap.from_obstacles(
        5,
        3,
        {
            (0, 0),
            (0, 2),
            (1, 0),
            (1, 2),
            (2, 0),
            (2, 2),
            (3, 0),
            (3, 2),
            (4, 0),
            (4, 1),
            (4, 2),
        },
    )

    assert escape_option_count(open_grid, (2, 2)) >= escape_option_count(dead_end_grid, (3, 1))


def test_irreversibility_is_independent_from_risk_layer():
    obstacles = {(1, 0), (1, 2), (2, 0), (2, 2)}
    low_risk = GridMap.from_obstacles(4, 3, obstacles)
    high_risk = GridMap.from_obstacles(4, 3, obstacles, risk={(2, 1): 1.0})

    low = analyze_recoverability(low_risk, (2, 1), {(0, 1)})
    high = analyze_recoverability(high_risk, (2, 1), {(0, 1)})
    assert low == high


def test_shortest_mode_matches_geometric_shortest_path_length():
    grid = GridMap.from_obstacles(6, 4)
    result = recoverability_astar(grid, (0, 0), (5, 3), mode=PlannerMode.SHORTEST)

    assert result.success
    assert result.geometric_length == 8
    assert result.cost == 8.0


def test_risk_aware_mode_avoids_high_risk_short_route():
    risk = {(x, 1): 1.0 for x in range(1, 5)}
    grid = GridMap.from_obstacles(6, 3, risk=risk)
    start, goal = (0, 1), (5, 1)

    shortest = recoverability_astar(grid, start, goal, mode=PlannerMode.SHORTEST)
    safer = recoverability_astar(
        grid,
        start,
        goal,
        mode=PlannerMode.RISK_AWARE,
        config=RecoverabilityAStarConfig(risk_weight=10.0),
    )

    assert shortest.success and safer.success
    assert safer.cumulative_risk < shortest.cumulative_risk
    assert safer.geometric_length >= shortest.geometric_length


def test_zero_weights_recover_shortest_objective():
    grid = GridMap.from_obstacles(5, 5, risk={(2, 2): 1.0})
    config = RecoverabilityAStarConfig(risk_weight=0.0, irreversibility_weight=0.0)

    shortest = recoverability_astar(grid, (0, 0), (4, 4), mode=PlannerMode.SHORTEST, config=config)
    proposed = recoverability_astar(grid, (0, 0), (4, 4), mode=PlannerMode.PROPOSED, config=config)

    assert shortest.success and proposed.success
    assert shortest.cost == proposed.cost
    assert shortest.geometric_length == proposed.geometric_length


def test_all_four_ablation_modes_return_auditable_metrics():
    grid = GridMap.from_obstacles(7, 5, obstacles={(3, 0), (3, 1), (3, 3), (3, 4)})
    for mode in PlannerMode:
        result = recoverability_astar(grid, (0, 2), (6, 2), mode=mode)
        assert result.success
        assert result.path[0] == (0, 2)
        assert result.path[-1] == (6, 2)
        assert result.geometric_length > 0
        assert result.minimum_escape_options >= 1
        assert result.planning_time_ms >= 0.0


def test_planning_latency_includes_recoverability_field_construction(monkeypatch):
    grid = GridMap.from_obstacles(5, 5)
    original_recoverability_map = recoverability_astar_module.recoverability_map
    timer_started = False
    clock = iter((100.0, 100.025))

    def fake_perf_counter() -> float:
        nonlocal timer_started
        timer_started = True
        return next(clock)

    def instrumented_recoverability_map(*args, **kwargs):
        assert timer_started, "planner timer must start before recoverability-map construction"
        return original_recoverability_map(*args, **kwargs)

    monkeypatch.setattr(recoverability_astar_module.time, "perf_counter", fake_perf_counter)
    monkeypatch.setattr(recoverability_astar_module, "recoverability_map", instrumented_recoverability_map)

    result = recoverability_astar_module.recoverability_astar(
        grid,
        (0, 0),
        (4, 4),
        mode=PlannerMode.RECOVERABILITY_AWARE,
    )

    assert result.success
    assert result.planning_time_ms == pytest.approx(25.0)
