from dynnav.planners import GridMap, self_aware_astar
from dynnav.planners.predictive_self_aware_astar import (
    PredictiveSelfAwareAStarWeights,
    predictive_self_aware_astar,
)
from dynnav.prediction import ConstantVelocityRiskPredictor, MovingRiskSource, PredictiveRiskMap


def test_predictive_risk_map_queries_time_indexed_risk():
    risk_map = PredictiveRiskMap(width=5, height=3, horizon=3, risk_layers={2: {(2, 1): 0.9}})

    assert risk_map.risk_at((2, 1), 0) == 0.0
    assert risk_map.risk_at((2, 1), 2) == 0.9
    assert risk_map.risk_at((99, 99), 2) == 1.0


def test_constant_velocity_predictor_moves_risk_source():
    grid = GridMap.from_obstacles(width=6, height=3)
    predictor = ConstantVelocityRiskPredictor(
        sources=(MovingRiskSource(position=(1, 1), velocity=(1, 0), risk=0.85),)
    )

    predicted = predictor.predict(grid, horizon=3)

    assert predicted.risk_at((1, 1), 0) == 0.85
    assert predicted.risk_at((2, 1), 1) == 0.85
    assert predicted.risk_at((3, 1), 2) == 0.85


def test_predictive_planner_avoids_future_hazard_on_short_path():
    grid = GridMap.from_obstacles(width=5, height=2)
    predictive_risk = PredictiveRiskMap(
        width=5,
        height=2,
        horizon=5,
        risk_layers={
            1: {(1, 0): 0.9},
            2: {(2, 0): 0.9},
            3: {(3, 0): 0.9},
        },
    )

    static_result = self_aware_astar(grid, (0, 0), (4, 0))
    predictive_result = predictive_self_aware_astar(
        grid,
        predictive_risk,
        (0, 0),
        (4, 0),
        PredictiveSelfAwareAStarWeights(predicted_risk_cost=12.0, current_risk_cost=0.0),
    )

    assert static_result.success
    assert predictive_result.success
    assert static_result.path == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    assert (1, 0) not in predictive_result.path
    assert (2, 0) not in predictive_result.path
    assert (3, 0) not in predictive_result.path
    assert predictive_result.path[0] == (0, 0)
    assert predictive_result.path[-1] == (4, 0)
