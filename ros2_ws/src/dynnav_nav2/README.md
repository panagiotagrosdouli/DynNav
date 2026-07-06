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
- string publisher for planned grid paths.

Not implemented yet:

- full Nav2 global planner plugin,
- costmap conversion,
- `nav_msgs/Path` output,
- action server integration,
- TF frame handling,
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

The bridge publishes a simple string representation of the planned grid path on:

```text
/dynnav/planned_path
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
```

## Next milestone

The next integration milestone is to replace the string publisher with:

- `nav_msgs/Path` output,
- occupancy-grid to `GridMap` conversion,
- a service or action interface,
- eventually a Nav2-compatible planner plugin.
