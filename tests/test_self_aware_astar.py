from dynnav.planners import GridMap, SelfAwareAStarWeights, astar, self_aware_astar


def test_astar_finds_shortest_path_on_empty_grid():
    grid = GridMap.from_obstacles(width=4, height=3)

    result = astar(grid, (0, 0), (3, 0))

    assert result.success
    assert result.path == [(0, 0), (1, 0), (2, 0), (3, 0)]
    assert result.cost == 3.0


def test_self_aware_astar_avoids_high_risk_corridor():
    risk = {
        (1, 0): 0.9,
        (2, 0): 0.9,
    }
    uncertainty = {
        (0, 1): 0.7,
        (1, 1): 0.7,
        (2, 1): 0.7,
        (3, 1): 0.7,
    }
    grid = GridMap.from_obstacles(width=4, height=2, risk=risk, uncertainty=uncertainty)

    baseline = astar(grid, (0, 0), (3, 0))
    aware = self_aware_astar(
        grid,
        (0, 0),
        (3, 0),
        SelfAwareAStarWeights(
            risk_cost=10.0,
            uncertainty_cost=0.2,
            low_recoverability_cost=4.0,
            information_gain_reward=0.5,
        ),
    )

    assert baseline.success
    assert aware.success
    assert baseline.path == [(0, 0), (1, 0), (2, 0), (3, 0)]
    assert (1, 0) not in aware.path
    assert (2, 0) not in aware.path
    assert aware.path[0] == (0, 0)
    assert aware.path[-1] == (3, 0)


def test_grid_rejects_invalid_risk_value():
    try:
        GridMap.from_obstacles(width=3, height=3, risk={(1, 1): 1.2})
    except ValueError as exc:
        assert "risk value" in str(exc)
    else:
        raise AssertionError("expected invalid risk to raise ValueError")
