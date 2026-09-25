from __future__ import annotations

from pathlib import Path

from dynnav_nav2_benchmark.correlated_history_execution import (
    blocker_footprint_cells,
    load_correlated_history_execution_suite,
)


def test_correlated_history_suite_parses_two_hazards(tmp_path: Path) -> None:
    path = tmp_path / "suite.yaml"
    path.write_text(
        """
schema_version: 1
seed: 20260925
gazebo:
  world_name: default
  robot_entity: turtlebot3_waffle
  blocker:
    parking_pose: {x: 100.0, y: 100.0, z: 0.5, yaw: 0.0}
    size: {x: 0.35, y: 1.20, z: 1.0}
planners: [DynNavShortest, DynNavHistory, DynNavRobustHistory]
scenario:
  name: correlated_return
  frame_id: map
  start: {x: -2.0, y: -0.5, yaw: 0.0}
  goal: {x: 1.75, y: 1.0, yaw: 0.0}
  safe_region:
    center: {x: -2.0, y: -0.5, yaw: 0.0}
    radius_m: 0.35
  dependence_conditions: [independent, common_cause, anti_correlated]
  pairwise_joint_lower: 0.0
  pairwise_joint_upper: 0.5
  recoverability_weight: 12.0
  minimum_injection_clearance_m: 0.9
  recovery_budget_m: 5.0
  reset_pose_tolerance_m: 0.4
  execution_timeout_s: 75.0
  wall_timeout_s: 150.0
  hazards:
    - blocker_entity: dynnav_corr_blocker_0
      action_trigger:
        hazard_id: h0
        source: {x: -1.275, y: -0.525, yaw: 0.0}
        target: {x: -1.225, y: -0.525, yaw: 0.0}
        closure_probability: 0.5
      blocker_pose: {x: -0.95, y: -0.425, z: 0.5, yaw: 0.0}
    - blocker_entity: dynnav_corr_blocker_1
      action_trigger:
        hazard_id: h1
        source: {x: -1.375, y: 0.475, yaw: 0.0}
        target: {x: -1.325, y: 0.475, yaw: 0.0}
        closure_probability: 0.5
      blocker_pose: {x: 0.9, y: -0.1, z: 0.5, yaw: 0.0}
""",
        encoding="utf-8",
    )

    suite = load_correlated_history_execution_suite(path)
    assert suite.planner_ids == (
        "DynNavShortest",
        "DynNavHistory",
        "DynNavRobustHistory",
    )
    assert len(suite.scenario.hazards) == 2
    assert suite.scenario.dependence_conditions == (
        "independent",
        "common_cause",
        "anti_correlated",
    )
    assert suite.blocker_size == (0.35, 1.2, 1.0)


def test_blocker_footprint_rasterizes_physical_rectangle() -> None:
    from dynnav_nav2_benchmark.dynamic_analysis import Pose3D

    cells = blocker_footprint_cells(
        center=Pose3D(1.0, 2.0, 0.5, 0.0),
        size_xy=(0.4, 1.0),
        origin_x=0.0,
        origin_y=0.0,
        resolution=0.2,
    )
    assert (4, 7) in cells
    assert (6, 12) in cells
    assert len(cells) == 18
