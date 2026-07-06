# DynNav ROS 2 / Nav2 Integration Scaffold

This package is the first ROS 2 integration layer for DynNav.

## Purpose

The existing DynNav algorithms are intentionally dependency-light Python research modules. This ROS 2 package keeps that core separate while exposing a bridge node that can be extended toward Nav2 integration.

## Current status

Readiness: **Scaffold / prototype**

Implemented:

- ROS 2 Python package structure,
- `dynnav_planner_bridge` node,
- YAML configuration,
- launch file,
- bridge from ROS parameters to the DynNav `self_aware_astar` research core,
- debug string publisher for planned grid paths,
- `nav_msgs/Path` publisher on `/dynnav/path`,
- grid-cell to map-frame coordinate conversion.

Not implemented yet:

- full Nav2 global planner plugin,
- costmap conversion,
- action server integration,
- TF frame handling beyond configurable `frame_id`,
- robot execution or controller integration.

## Build

From the repository root, assuming a sourced ROS 2 environment:

```bash
cd ros2_ws
colcon build --packages-select dynnav_nav2
source install/setup.bash
```

## Run

```bash
ros2 launch dynnav_nav2 dynnav_planner_bridge.launch.py
```

The bridge publishes:

```text
/dynnav/planned_path   # std_msgs/String debug path
/dynnav/path           # nav_msgs/Path planner output
```

## Configuration

Edit:

```text
ros2_ws/src/dynnav_nav2/config/dynnav_planner_bridge.yaml
```

Example:

```yaml
dynnav_planner_bridge:
  ros__parameters:
    grid_width: 10
    grid_height: 10
    start: "0:0"
    goal: "9:9"
    obstacles: "3:3,3:4,3:5"
    resolution_m: 1.0
    frame_id: "map"
```

## Next milestone

The next integration milestone is to add:

- occupancy-grid to `GridMap` conversion,
- a service or action interface,
- eventually a Nav2-compatible planner plugin.
