# DynNav C++ Nav2 Plugin Skeleton

This package is a scaffold for a future Nav2-compatible DynNav global planner plugin.

## Current status

Readiness: **skeleton only**

Implemented:

- C++ ROS 2 package structure,
- `nav2_core::GlobalPlanner` class skeleton,
- pluginlib export file,
- CMake setup,
- no-op lifecycle methods,
- placeholder `createPlan()` that returns a direct two-pose path.

Not implemented yet:

- costmap conversion,
- DynNav planner backend integration,
- risk / uncertainty / information-gain objective,
- collision checking,
- parameter loading,
- simulation validation.

## Build

From the ROS 2 workspace:

```bash
cd ros2_ws
colcon build --packages-select dynnav_nav2_cpp
source install/setup.bash
```

## Intended Nav2 configuration

A future planner-server configuration should load:

```yaml
planner_server:
  ros__parameters:
    planner_plugins: ["DynNavPlanner"]
    DynNavPlanner:
      plugin: "dynnav_nav2_cpp/DynNavGlobalPlanner"
```

## Next milestone

Replace the placeholder direct path with a costmap-backed grid planner, then connect the self-aware DynNav objective.
