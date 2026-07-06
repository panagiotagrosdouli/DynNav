# DynNav Nav2 Plugin Architecture

This document describes how DynNav should evolve from a ROS 2 bridge into a real Nav2-compatible global planner plugin.

## Goal

The long-term goal is to expose DynNav planning through the Nav2 planner server interface, so that a robot can request paths from DynNav using the standard Nav2 stack.

## Target interface

A production plugin should implement the Nav2 global planner interface:

```cpp
nav2_core::GlobalPlanner
```

The planner should provide:

- `configure(...)`
- `activate()`
- `deactivate()`
- `cleanup()`
- `createPlan(start, goal)`

## Proposed architecture

```text
Nav2 planner server
        |
        v
DynNavGlobalPlanner plugin
        |
        v
Costmap / OccupancyGrid adapter
        |
        v
DynNav planning backend
        |
        v
nav_msgs/Path
```

## Bridge vs plugin

The current Python bridge is useful for research and fast prototyping. A Nav2 plugin is different:

| Layer | Purpose |
|---|---|
| Python bridge | Fast research iteration and simple ROS testing. |
| C++ Nav2 plugin | Real Nav2 planner-server integration. |
| DynNav core | Algorithmic planning logic and benchmarkable research code. |

## Data conversion responsibilities

The plugin should convert:

- Nav2 costmap cells to DynNav grid cells,
- occupancy or cost values to risk,
- unknown cells to uncertainty,
- DynNav grid path to `nav_msgs/Path`.

## First skeleton milestone

This PR adds only architecture documentation and a minimal C++ package skeleton. It is not yet a working plugin.

## Next implementation milestones

1. Add compilable C++ plugin package.
2. Add `pluginlib` export XML.
3. Implement lifecycle methods with no-op behavior.
4. Add simple straight-line or grid fallback plan.
5. Connect costmap conversion.
6. Replace fallback plan with DynNav planner backend.
7. Add Nav2 launch example.
8. Add simulation smoke test.

## Scientific value

A Nav2 plugin makes DynNav much more credible as a robotics system because it can be evaluated in the same stack used by real mobile robots. This is a necessary step before Gazebo, Isaac Sim, or real robot experiments.
