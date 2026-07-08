"""Tests for lab-grade DynNav research primitives."""

from __future__ import annotations

import numpy as np

from dynnav.core import GridMap, Pose, Trajectory
from dynnav.lab_grade import (
    FeatureMaturity,
    FEATURE_REGISTRY,
    PlanningRequest,
    ReroutingSupervisor,
    SafetySupervisor,
    astar_plan,
    blocked_path,
    build_fields,
    compute_proximity_risk,
    compute_uncertainty_field,
    dijkstra_plan,
    run_single_research_episode,
)


def _open_grid() -> GridMap:
    grid = np.zeros((5, 5), dtype=float)
    grid[2, 1:4] = 1.0
    grid[2, 2] = 0.0
    return GridMap(grid)


def test_feature_registry_is_scientifically_honest() -> None:
    statuses = {feature.maturity for feature in FEATURE_REGISTRY}
    assert FeatureMaturity.IMPLEMENTED in statuses
    assert FeatureMaturity.PROTOTYPE in statuses
    assert FeatureMaturity.PLANNED in statuses
    assert all(feature.limitation for feature in FEATURE_REGISTRY)


def test_astar_and_dijkstra_find_paths() -> None:
    grid = _open_grid()
    start = Pose(0, 0)
    goal = Pose(4, 4)
    astar, astar_expanded = astar_plan(grid, start, goal)
    dijkstra, dijkstra_expanded = dijkstra_plan(grid, start, goal)
    assert astar.poses[0] == start and astar.poses[-1] == goal
    assert dijkstra.poses[0] == start and dijkstra.poses[-1] == goal
    assert astar.cost <= dijkstra.cost
    assert astar_expanded <= dijkstra_expanded


def test_risk_uncertainty_and_recoverability_fields_are_normalized() -> None:
    request = PlanningRequest(start=Pose(0, 0), goal=Pose(4, 4), occupancy=_open_grid())
    fields = build_fields(request)
    fields.validate()
    assert fields.risk.shape == (5, 5)
    assert fields.uncertainty.shape == (5, 5)
    assert fields.recoverability.shape == (5, 5)
    assert 0.0 <= fields.recoverability[0, 0] <= 1.0


def test_uncertainty_is_high_for_unknown_cells() -> None:
    grid = GridMap(np.full((3, 3), 0.5))
    field = compute_uncertainty_field(grid)
    assert np.allclose(field, 1.0)


def test_dynamic_obstacle_increases_local_risk() -> None:
    grid = GridMap(np.zeros((5, 5)))
    risk = compute_proximity_risk(grid, dynamic_obstacles=(Pose(2, 2),))
    assert risk[2, 2] > risk[0, 0]


def test_blocked_path_detects_dynamic_obstacle() -> None:
    path = (Pose(0, 0), Pose(1, 0), Pose(2, 0))
    grid = GridMap(np.zeros((3, 3)))
    assert blocked_path(path, grid, dynamic_obstacles=(Pose(1, 0),))


def test_safety_supervisor_modes() -> None:
    supervisor = SafetySupervisor()
    assert supervisor.decide(risk=0.9, uncertainty=0.1, recoverability=1.0).mode == "SAFE_STOP"
    assert supervisor.decide(risk=0.2, uncertainty=0.1, recoverability=0.1).mode == "SAFE_MODE"
    assert supervisor.decide(risk=0.6, uncertainty=0.1, recoverability=0.8).mode == "REPLAN"
    assert supervisor.decide(risk=0.1, uncertainty=0.1, recoverability=0.8).mode == "NOMINAL"


def test_rerouting_supervisor_respects_cooldown() -> None:
    grid = _open_grid()
    request = PlanningRequest(start=Pose(0, 0), goal=Pose(4, 4), occupancy=grid)
    fields = build_fields(request)
    supervisor = ReroutingSupervisor(risk_threshold=0.1, cooldown_steps=3)
    trajectory = Trajectory((Pose(0, 0), Pose(1, 0)), cost=1.0, risk=0.9, recoverability=1.0)
    first = supervisor.evaluate(1, trajectory, fields, Pose(0, 0), trajectory.poses)
    second = supervisor.evaluate(2, trajectory, fields, Pose(0, 0), trajectory.poses)
    assert first.should_reroute
    assert not second.should_reroute
    assert second.cooldown_active


def test_research_episode_reports_metrics() -> None:
    metrics = run_single_research_episode(
        PlanningRequest(start=Pose(0, 0), goal=Pose(4, 4), occupancy=_open_grid(), seed=13)
    )
    assert metrics["seed"] == 13
    assert metrics["path_found"] is True
    assert metrics["path_length"] > 0
    assert metrics["planning_time_ms"] >= 0.0
