# OccupancyGrid to DynNav GridMap Conversion

This document explains the first conversion layer from ROS-style occupancy grids to the DynNav research-core `GridMap`.

## Purpose

DynNav planners operate on `GridMap`, while ROS navigation stacks commonly expose environment data as `nav_msgs/OccupancyGrid` or costmap-like grids.

This conversion layer is a step toward using real ROS map inputs instead of manually configured obstacle strings.

## Conversion policy

ROS OccupancyGrid convention:

| Value | Meaning | DynNav handling |
|---:|---|---|
| `-1` | unknown | uncertainty = 1.0, risk = 0.5 |
| `0` | free | risk = 0.0 |
| `1..100` | occupancy probability / cost | risk = value / 100 |

A cell is marked as an obstacle when:

```text
value >= occupied_threshold
```

The default threshold is `65`.

Unknown cells can optionally be treated as obstacles using:

```python
unknown_is_obstacle=True
```

## Why uncertainty matters

Unknown cells are not always hard obstacles. Treating them as high uncertainty allows DynNav planners to decide whether to avoid, explore, or actively gather information depending on the task objective.

## Current status

Implemented:

- ROS-free `OccupancyGridSpec`,
- row-major index conversion,
- occupancy-to-risk conversion,
- unknown-cell uncertainty mapping,
- optional unknown-as-obstacle policy,
- conversion into `GridMap`,
- tests independent of a ROS runtime.

Not implemented yet:

- live `/map` subscription,
- costmap topic integration,
- TF-aware origin handling,
- inflation-layer interpretation,
- Nav2 plugin integration.

## Next milestone

The next ROS milestone is to add a map subscriber to `dynnav_planner_bridge` and allow the planner to use a received occupancy grid instead of only YAML-configured obstacle cells.
