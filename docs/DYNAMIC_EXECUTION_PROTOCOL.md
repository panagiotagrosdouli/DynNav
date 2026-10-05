# Dynamic route-invalidation protocol

## Status and purpose

This protocol implements the first real `NavigateToPose` execution layer for
DynNav on ROS 2 Jazzy, Nav2, TurtleBot3, and Gazebo Harmonic. It compares NavFn,
Smac 2D, DynNav risk-only, and joint risk-plus-local-irreversibility planners
under the same frozen obstacle events.

The runner, Gazebo service bridge, blocker model, scenario contract,
costmap-reachability oracle, package tests, and manual GitHub Actions workflow
are committed. The commissioning workflow passed as [run
31488640894](https://github.com/panagiotagrosdouli/DynNav/actions/runs/31488640894)
on branch head `253e3b3`; the complete artifact is retained under
[`results/ros2_gazebo/dynamic_run_31488640894/`](../results/ros2_gazebo/dynamic_run_31488640894/).
This is `n=1` protocol commissioning, not a powered hypothesis test.

## Operational irreversibility contract

At the declared event time, Gazebo moves a named physical blocker from a parking
pose into the route. After the fixed observation delay, the runner stores the
complete inflated Nav2 global costmap and the robot pose. An independent
eight-connected Dijkstra oracle then asks whether a path exists from that pose
to any traversable cell in the declared circular safe region.

For a frozen recovery-distance budget `B`, the recorded endpoint is:

```text
operational_irreversible_failure =
    no grid path to S_safe OR shortest recovery path length > B
```

Diagonal corner-cutting is prohibited. Cost `255` is unknown and rejected;
costs at or above `253` are non-traversable. The oracle does not use the planner
being evaluated.

This is an explicit, reproducible 2D costmap contract. It is not kinodynamic
viability, collision evidence, a formal safety proof, or physical-robot
irreversibility.

## Compared methods

| Planner ID | Role |
|---|---|
| `NavFn` | Established Dijkstra baseline |
| `Smac2D` | Established cost-aware A* baseline |
| `DynNavRisk` | Risk-only DynNav ablation |
| `DynNavJoint` | Risk plus local escape-option DynNav |

Every goal uses a generated Behavior Tree with an immutable explicit planner
ID. The tree otherwise preserves 1 Hz replanning, controller execution, and the
standard clearing, spin, wait, and backup recovery structure. The exact XML and
its SHA-256 are retained per planner.

## Frozen sandbox events

The current suite contains one proposed positive mechanism and one negative
control. Coordinates are frozen in
`config/sandbox_dynamic_events.yaml`.

| Scenario | Trigger | Blocker pose | Intended mechanism |
|---|---:|---:|---|
| `return_gate_closure` | 8.0 s | `(-0.95, -0.425)` | Close a narrow return gate after departure; active forward-path intersection is **not** required |
| `forward_closure_negative_control` | 4.0 s | `(0.9, -0.1)` | Block the active forward route without intentionally sealing the safe region; active-path intersection **is** required |

Both use the same red static box (`0.35 × 1.20 × 1.00 m`) and a 2.0 s
observation delay. A trial is invalid—not a planner failure—when:

- the robot is closer than the declared injection clearance;
- the first navigation feedback pose differs from the commanded reset pose by
  more than the declared tolerance;
- Gazebo rejects the entity move;
- navigation feedback is unavailable at the event;
- the number of lethal cells inside the blocker footprint plus its declared
  observation margin does not increase by the frozen minimum from the
  pre-event costmap;
- no post-event costmap/recovery assessment is captured;
- for a scenario declaring `require_forward_path_invalidation: true`, the
  blocker footprint does not intersect the active pre-event planner path.

The return-gate mechanism intentionally closes connectivity behind the departing
robot. It is therefore validated through blocker observation plus the
independent safe-region recovery oracle, not by requiring intersection with the
forward plan. The forward-closure negative control retains the active
path-invalidation requirement.

A genuine Nav2 terminal failure before the event is retained as a valid
pre-event method failure with no irreversibility assessment. A successful goal
that finishes before the event invalidates the scenario timing instead of being
silently counted as a dynamic success. If navigation terminates shortly after a
valid injection, the runner waits for the observation interval and still
captures the post-event costmap.

These coordinates passed the commissioning safety and observation guards in
8/8 trials. Minimum observed robot-to-blocker centre clearance was 0.955 m,
above the frozen 0.90 m threshold, and the blocker appeared in every archived
post-event costmap. If a geometry change is required, change the schema input
before collecting the final comparison dataset and do not pool results across
protocol versions.

## Reset and order controls

- The blocker is parked at `(100, 100)` before every trial.
- The TurtleBot3 entity is teleported to the frozen start pose.
- AMCL receives the same initial pose and both costmaps are cleared.
- A fixed reset-settle interval precedes each goal.
- Each repetition contains every planner once.
- Seeded cyclic counterbalancing keeps execution-position counts within one.
- Simulation and wall-clock timeouts are both recorded and enforced.
- Event timing uses Nav2 navigation time; wall time is only the hang guard.

Teleport reset is a simulation control, not a physical-robot procedure.

## Outcomes and failure taxonomy

The artifact keeps full feedback traces, Nav2 result code/message, number of
recoveries, event timing/clearance, global costmap snapshots, and both pooled
and scenario-stratified summaries.

| Field | Meaning |
|---|---|
| `planning_failure` | Nav2 terminal result code in the `ComputePathToPose` 200 range |
| `controller_failure` | Nav2 terminal result code in the `FollowPath` 100 range |
| `execution_timeout` | Frozen simulation or wall timeout was reached |
| `recovery_exhausted` | Navigation failed after at least one reported recovery |
| `operational_irreversible_failure` | Independent recovery oracle failed the frozen contract |
| `invalid_trial` | Event delivery or measurement contract was not satisfied |

These fields are not collapsed into one generic failure label.

## Run

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch dynnav_nav2_benchmark \
  tb3_dynamic_execution_benchmark.launch.py \
  headless:=true \
  repetitions:=1 \
  output_dir:=$PWD/results/nav2_dynamic
```

The manual workflow is `ROS 2 dynamic route-invalidation benchmark`. It returns
non-zero when any trial is invalid, while genuine navigation or operational
irreversibility failures remain valid experimental outcomes.

## Required progression before a PhD-result claim

1. Completed: retain a fully valid smoke artifact on a named branch head.
2. Inspect both scenarios in RViz/Gazebo and confirm the blocker mechanism.
3. Freeze protocol version 1 or revise it before confirmatory data collection.
4. Add at least 30 paired dynamic map/event seeds per mechanism after power
   analysis; repeated identical runs only measure runtime variability.
5. Add an independent collision/contact channel and minimum-clearance metric.
6. Report paired effects and confidence intervals per scenario, including
   invalid trials and negative results.
7. Replicate the frozen protocol on TurtleBot3 hardware only after adding an
   independent emergency stop and replacing teleport resets.

## Primary interface provenance

- Navigation2 Jazzy default recovery BT blob:
  `f135107c5b1c5267bf2190549d8b55eaafe0dc7d`
- Navigation2 Jazzy TurtleBot3 launch blob:
  `db1964f955e3fa98d69cace024b2ad37b03380d4`
- `ros_gz_interfaces/SetEntityPose.srv` blob:
  `b749488cca3ae907cfac39717d12cf5aad720227`
- `ros_gz_interfaces/SpawnEntity.srv` blob:
  `35d5df59e55f629f6ba45fece97627aae59e4aa9`
- Jazzy service support appears in `ros_gz_bridge` 1.0.11; the workflow archives
  the installed version rather than assuming it.

Primary sources:

- [Nav2 NavigateToPose action](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_msgs/action/NavigateToPose.action)
- [Nav2 ComputePathToPose action](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_msgs/action/ComputePathToPose.action)
- [Nav2 FollowPath action](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_msgs/action/FollowPath.action)
- [Jazzy ros_gz_bridge changelog](https://github.com/gazebosim/ros_gz/blob/jazzy/ros_gz_bridge/CHANGELOG.rst)
