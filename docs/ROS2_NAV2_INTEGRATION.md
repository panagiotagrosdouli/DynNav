# ROS 2 / Nav2 Integration

Status: **Prototype**

DynNav is structured so that risk-aware planning, uncertainty fields, recoverability scores, and mission supervision can be adapted to ROS 2 and Nav2. This document is deliberately conservative: no compiled Nav2 plugin or hardware-validated deployment is claimed until it exists in CI or a reproducible ROS workspace.

## Target integration architecture

```text
/map, /scan, /odom, /tf
        |
        v
Occupancy belief adapter
        |
        +--> uncertainty field
        +--> risk field
        +--> recoverability field
        |
        v
DynNav planner adapter  <---- Nav2 ComputePathToPose
        |
        v
Nav2 controller / behavior tree
        |
        v
Safety supervisor: nominal / replan / safe-mode / safe-stop
```

## Prototype package layout

Recommended future ROS workspace layout:

```text
ros2_ws/src/dynnav_nav2/
  package.xml
  CMakeLists.txt
  plugin.xml
  include/dynnav_nav2/risk_aware_planner.hpp
  src/risk_aware_planner.cpp
  launch/dynnav_nav2.launch.py
  config/nav2_params.yaml
  behavior_trees/dynnav_recovery.xml
  rviz/dynnav.rviz
```

## Topic contract

| Interface | Direction | Status | Purpose |
|---|---|---|---|
| `/map` | input | Prototype | Occupancy grid source |
| `/odom` | input | Prototype | Robot state estimate |
| `/tf` | input | Prototype | Frame transforms |
| `/dynnav/risk_grid` | output | Prototype | Risk visualization |
| `/dynnav/uncertainty_grid` | output | Prototype | Uncertainty visualization |
| `/dynnav/recoverability_grid` | output | Prototype | Recoverability visualization |
| `/dynnav/safety_mode` | output | Prototype | Supervisor state |
| `/dynnav/reroute_events` | output | Prototype | Rerouting diagnostics |

## Nav2 plugin scaffold requirements

A complete Nav2 planner plugin should:

1. implement `nav2_core::GlobalPlanner`;
2. convert `nav_msgs::msg::OccupancyGrid` into DynNav's `GridMap` or a C++ equivalent;
3. expose risk, uncertainty, and recoverability weights as ROS parameters;
4. publish debug grids for RViz;
5. return `nav_msgs::msg::Path`;
6. provide deterministic tests with a fixed occupancy grid;
7. be compiled in CI using a ROS 2 Docker image.

## Behavior tree scaffold

The behavior tree should expose a condition/action pair:

- `DynNavRiskAcceptable`: returns success when risk and uncertainty remain under thresholds.
- `DynNavTriggerReroute`: requests replanning when path blockage, high risk, high uncertainty, or low recoverability is detected.

## Parameter example

```yaml
dynnav_planner:
  ros__parameters:
    planner_id: dynnav_risk_aware_astar
    risk_weight: 4.0
    uncertainty_weight: 2.0
    recoverability_weight: 1.5
    risk_threshold: 0.55
    uncertainty_threshold: 0.70
    recoverability_threshold: 0.30
    reroute_cooldown_s: 1.0
    publish_debug_grids: true
```

## RViz visualization plan

RViz should display:

- map and local costmap;
- current global path;
- executed trajectory;
- risk heatmap;
- uncertainty heatmap;
- recoverability heatmap;
- dynamic obstacles;
- safety mode text marker;
- reroute event markers.

## Bag playback protocol

Future bag-based experiments should record:

```bash
ros2 bag record /map /scan /odom /tf /plan /cmd_vel \
  /dynnav/risk_grid /dynnav/uncertainty_grid \
  /dynnav/recoverability_grid /dynnav/safety_mode \
  /dynnav/reroute_events
```

## Current limitations

- No compiled C++ Nav2 planner plugin is claimed in this branch.
- No Gazebo, Isaac Sim, or hardware experiment is claimed as completed unless results are generated and committed.
- The Python implementation is the reference prototype for algorithms and tests.
- Real robot deployment requires additional safety validation, robot-specific dynamics, and emergency-stop integration.
