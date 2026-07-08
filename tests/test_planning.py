"""Tests for core DynNav planning behavior."""

from __future__ import annotations

import numpy as np

from dynnav.core import GridMap, Pose
from dynnav.monitoring import RuntimeMonitor, SafeModeSupervisor
from dynnav.planning import RiskAwareAStar
from dynnav.risk import cvar, propagate_uncertainty


def test_cvar_upper_tail() -> None:
    values = np.array([0.0, 1.0, 2.0, 100.0])
    assert cvar(values, alpha=0.75) == 100.0


def test_planner_finds_path_on_empty_grid() -> None:
    grid = GridMap(np.zeros((8, 8)))
    trajectory, metrics = RiskAwareAStar().plan(grid, Pose(0, 0), Pose(7, 7))
    assert metrics.path_found
    assert trajectory.poses[0] == Pose(0, 0)
    assert trajectory.poses[-1] == Pose(7, 7)
    assert trajectory.risk < 0.1


def test_monitor_switches_to_stop_for_local_obstacle() -> None:
    occupancy = np.zeros((5, 5))
    occupancy[2, 2] = 0.9
    grid = GridMap(occupancy)
    trajectory, _ = RiskAwareAStar().plan(grid, Pose(0, 0), Pose(4, 4))
    mode = SafeModeSupervisor(RuntimeMonitor()).mode(grid, Pose(2, 2), trajectory)
    assert mode == "stop"


def test_uncertainty_propagation_bounds() -> None:
    updated = propagate_uncertainty(np.array([[0.0, 1.0]]), process_noise=0.2)
    assert updated.min() >= 0.0
    assert updated.max() <= 1.0
