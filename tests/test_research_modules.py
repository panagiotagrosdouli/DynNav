import numpy as np

from dynnav.core import GridMap, Pose, Trajectory
from dynnav.research_modules import (
    DynNavResearchStack,
    MissionRiskEstimator,
    RuntimeMonitor,
    RuntimeObservation,
    SafetyMode,
    UncertaintyPropagator,
    UncertaintyState,
)


def test_uncertainty_propagation_increases_dynamic_cell_risk() -> None:
    grid = GridMap(np.zeros((6, 6), dtype=float))
    propagated = UncertaintyPropagator(process_noise=0.0).propagate(
        grid,
        dynamic_cells=[Pose(3, 3)],
    )

    assert propagated.probability(Pose(3, 3)) > grid.probability(Pose(3, 3))
    assert propagated.occupancy.shape == grid.occupancy.shape


def test_mission_risk_estimator_selects_safe_mode_for_poor_recoverability() -> None:
    trajectory = Trajectory((Pose(0, 0), Pose(1, 0)), cost=2.0, risk=0.2, recoverability=0.1)
    uncertainty = UncertaintyState(0.1, 0.1, 0.1, 0.1)

    report = MissionRiskEstimator().evaluate(trajectory, uncertainty)

    assert report.recommended_mode == SafetyMode.SAFE_MODE
    assert 0.0 <= report.mission_score <= 1.0


def test_runtime_monitor_cooldown_suppresses_repeated_replans() -> None:
    trajectory = Trajectory((Pose(0, 0), Pose(1, 0)), cost=2.0, risk=0.55, recoverability=0.8)
    uncertainty = UncertaintyState(0.1, 0.1, 0.1, 0.1)
    monitor = RuntimeMonitor(cooldown=5)

    first = monitor.observe(RuntimeObservation(1, Pose(0, 0), 0.55, 0.8, uncertainty), trajectory)
    second = monitor.observe(RuntimeObservation(2, Pose(0, 0), 0.55, 0.8, uncertainty), trajectory)

    assert first.mode == SafetyMode.REPLAN
    assert second.mode == SafetyMode.CAUTIOUS


def test_research_stack_returns_trajectory_and_report() -> None:
    grid = GridMap(np.zeros((8, 8), dtype=float))
    stack = DynNavResearchStack()
    trajectory, report = stack.plan_and_evaluate(
        grid,
        Pose(0, 0),
        Pose(7, 7),
        UncertaintyState(0.1, 0.1, 0.1, 0.0),
    )

    assert trajectory.length > 1
    assert report.recommended_mode in set(SafetyMode)
