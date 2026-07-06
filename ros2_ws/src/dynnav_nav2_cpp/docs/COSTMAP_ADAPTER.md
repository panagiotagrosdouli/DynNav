# C++ Costmap Adapter Skeleton

This document describes the first costmap adapter layer for the DynNav Nav2 plugin skeleton.

## Purpose

Nav2 planners receive environment information through costmaps. DynNav planners reason about grid cells, risk, uncertainty, and occupancy. The adapter is the boundary between these representations.

## Implemented mappings

| Nav2 cost value | DynNav interpretation |
|---:|---|
| `255` | unknown, risk `0.5`, uncertainty `1.0` |
| `0` | free, risk `0.0`, uncertainty `0.0` |
| `1..253` | normalized risk `cost / 253` |
| `>= lethal_threshold` | occupied, except unknown |

## Implemented helpers

- `costToRisk(cost)`
- `costToUncertainty(cost)`
- `isOccupiedCost(cost, lethal_threshold)`
- `indexToCell(index, width)`

## Current status

Readiness: **adapter skeleton**

This PR does not yet read the full Nav2 costmap object inside `createPlan()`. It only introduces the conversion policy and helper functions so the next PR can connect costmap reads to the planner path generation.

## Next milestone

- Read `nav2_costmap_2d::Costmap2D` from the plugin.
- Convert all costmap cells into a `DynNavCostmapSnapshot`.
- Use the snapshot inside `createPlan()`.
- Replace placeholder straight-line path with costmap-aware grid planning.
