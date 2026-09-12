from __future__ import annotations

import pytest

from dynnav.planners.grid_map import GridMap
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.recoverability_belief import TopologyHazardBelief


def test_all_modes_reduce_to_shortest_length_without_hazards() -> None:
    grid = GridMap.from_obstacles(6, 4)
    start, goal = (0, 0), (5, 3)
    hazard = TopologyHazardBelief({})

    results = [
        hazard_reliability_astar(grid, start, goal, hazard=hazard, mode=mode)
        for mode in HazardReliabilityMode
    ]

    assert all(result.success for result in results)
    assert {result.geometric_length for result in results} == {8}
    assert all(result.minimum_estimated_return_probability == pytest.approx(1.0) for result in results)


def test_zero_reliability_weight_recovers_geometric_objective() -> None:
    grid = GridMap.from_obstacles(5, 3)
    hazard = TopologyHazardBelief({(2, 1): 0.8})
    config = HazardReliabilityAStarConfig(reliability_weight=0.0)

    shortest = hazard_reliability_astar(
        grid,
        (0, 1),
        (4, 1),
        hazard=hazard,
        mode=HazardReliabilityMode.SHORTEST,
        config=config,
    )
    reliability = hazard_reliability_astar(
        grid,
        (0, 1),
        (4, 1),
        hazard=hazard,
        mode=HazardReliabilityMode.REDUNDANT_RETURN,
        config=config,
    )

    assert shortest.success and reliability.success
    assert shortest.geometric_length == reliability.geometric_length
    assert shortest.cost == pytest.approx(reliability.cost)


def test_reliability_metrics_are_bounded_on_success() -> None:
    grid = GridMap.from_obstacles(6, 6, obstacles={(2, 2), (3, 2), (2, 3)})
    hazard = TopologyHazardBelief({(1, 3): 0.4, (4, 3): 0.6, (3, 4): 0.2})

    result = hazard_reliability_astar(
        grid,
        (0, 0),
        (5, 5),
        hazard=hazard,
        mode=HazardReliabilityMode.REDUNDANT_RETURN,
    )

    assert result.success
    assert 0.0 <= result.minimum_estimated_return_probability <= 1.0
    assert result.cumulative_return_fragility >= 0.0
    assert result.planning_time_ms >= 0.0


def test_invalid_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="reliability_weight"):
        HazardReliabilityAStarConfig(reliability_weight=-1.0).validate()
