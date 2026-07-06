# DynNav Planning Request Interface

This document describes the first planning-request interface scaffold for the ROS 2 integration layer.

## Purpose

The current bridge can periodically publish a planned path. The next integration target is an explicit planning request interface, where another ROS node can ask DynNav for a plan on demand.

## Current scaffold

Implemented in this PR:

- request string parsing helpers,
- response string formatting helpers,
- tests for request and response formatting.

The lightweight request format is:

```text
start_x:start_y;goal_x:goal_y
```

Example:

```text
0:0;9:9
```

A successful response is formatted as:

```text
OK: (0,0) -> (1,0) -> (2,0)
```

A failed response is formatted as:

```text
FAILED: no path
```

## Intended ROS interface

The intended next implementation is a small ROS 2 service endpoint:

```text
/dynnav/plan
```

The first version can use `std_srvs/Trigger` for smoke testing. A later version should replace it with a custom request type containing:

- start pose or start grid cell,
- goal pose or goal grid cell,
- planner mode,
- whether to use the live map,
- optional timeout.

## Why this matters

An explicit request interface is closer to Nav2 planner semantics than only publishing a path periodically. It also makes DynNav easier to test from launch files, integration tests, and simulation nodes.

## Next milestone

Add the actual ROS service node once the package interface is ready, then replace the string format with a typed service or Nav2-compatible action/plugin API.
