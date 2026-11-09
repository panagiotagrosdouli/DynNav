# C01 — Physical Robot Study Protocol (NOT EXECUTED)

This protocol applies **only to C01 Learned A***. It is a commissioning and
measurement design, **not** a report of successful hardware trials.

Current physical trials: **0 verified**. Hardware platform: **not yet supplied or
verified**. No rosbag, serial/robot identifier or authenticated C01 controller
trace has been provided.

## A. Prerequisites and safety gate

- Record actual robot model, ROS 2 distribution, controller, sensor set,
  safety stop type, firmware, battery, radio link, map and calibration.
- Require trained onsite operator and an independently functioning physical
  emergency stop, tested before autonomous commands are enabled.
- Use a closed controlled environment, low speed, ample robot footprint/
  inflation clearance and a clear exclusion zone; no human-proximity or
  deliberate collision experiments.
- Confirm `/tf`, `/tf_static`, `/odom`, `/scan`,
  `/amcl_pose` (or documented localization alternative), lifecycle nodes,
  costmap freshness and map registration.
- Inspect an approved C01-to-Nav2 adapter and its evidence that raw or clipped
  learned A* actually produced each planned path. A working C00 C++ Nav2
  plugin does **not** constitute a C01 neural heuristic adapter.
- Require the local safety engineer/operator to approve actual experiment
  execution. Any failure to cancel, localize, stop or maintain adequate
  clearance ends the trial; retain as incident.

## B. Commissioning gates (performed on actual robot by operator)

1. Wheels isolated / robot immobilized: verify scan orientation, command
   routing, kill/stop circuit and ROS time/TF synchronization.
2. Low-speed manual move: validate odometry, footprint, costs and stopping.
3. Onboard default Nav2 planner in a short static clear route: verify the
   navigation controller and independent stop. This is a platform control,
   not a C01 performance result.
4. With motion disabled, compute matched C01 Manhattan/raw/clipped paths on
   the same robot costmap. Confirm the actual loaded checkpoint digest and
   no fallback; run independent plan correctness checks.
5. After operator sign-off, execute short validated path tasks one planner
   at a time, at approved speed; do not inject moving obstacles or closure
   mechanisms in the initial C01 hardware study.

## C. Freeze the comparison before outcomes

Pre-register task IDs, map and checkpoint digests, start/goal poses, goal
tolerance, minimum clearances, controller and velocity limits, seeds,
exclusion rules, restart/reset procedure, failure criteria, timing contracts,
and primary endpoints.

Main planner variants:
- Manhattan A* (optimal on a four-connected unit-cost grid).
- Saved raw learned A* (optimality **not guaranteed**).
- Manhattan-clipped learned A* (admissible on the grid model, not necessarily
  faster or consistent).
- Dijkstra as an optional offline validation reference.

For each block, use the same robot and map, matched start/goal and randomized
planner order. Record map changes and conditions; repeat when safe and
predeclared. Never retrospectively remove valid failures or select only
successful endpoints.

## D. Minimum recorded evidence

Retain a manifest for **each actual robot run**:

| Required field | Purpose |
|---|---|
| `trial_id`, `block_id`, `planner_mode` | Pairing and method |
| `git_sha`, `container_image`, `ros_distro` | Software provenance |
| `robot_model`, `robot_id`, `sensor_ids` | Actual physical platform |
| `map_sha256`, `model_sha256` | Inputs, checkpoint identity |
| `start_pose`, `goal_pose`, `controller_parameters` | Controlled task |
| `operator_id`, `safety_approval`, `e_stop_check` | Human hardware safety gate |
| `rosbag_path`, `rosbag_sha256` | Independently inspectable sensor record |
| `planner_trace_path`, `planner_trace_sha256` | Proof the chosen C01 method actually ran |
| `planned_path`, `executed_path`, `timestamps` | Planning vs motion |
| `status`, `validity_reason`, `incident` | Success, failure and exclusions |

Record sensor topics appropriate to the platform. A starting point is
`/tf /tf_static /odom /scan /cmd_vel /amcl_pose /plan`, plus
costmap topics, Nav2 lifecycle status, C01 planner mode and checkpoint ID,
telemetry diagnostics, stop events and localization confidence.

Never store personal operator identifiers in a public artifact if
not necessary; use pseudonymous trial records and retain restricted logs
securely.

## E. Metrics and controls

Primary physical outcomes:
- Navigation success rate with predeclared terminal criteria.
- Physical route length computed from actual odometry or appropriately
  aligned ground truth, including localization uncertainty.
- Navigation duration and cancellation/stop occurrences.
- Safety-relevant minimum clearance if actually measured with a calibrated
  sensor setup; otherwise mark unavailable.

Secondary planning outcomes:
- Planner expansions, per-query latency including necessary inference,
  checkpoint load latency separately, CPU/GPU, memory, plan validity,
  path-cost difference against consistent optimal reference.

Use within-task paired comparisons. Report per-trial data, paired
differences, confidence intervals and invalid-trial reasons, without
pseudo-replicating multiple sensor timestamps as independent missions.

**A physical trial may fail; this is scientifically valid evidence and must
not be omitted.**

## F. Stop criteria

Immediate operator-controlled stop and no automatic retry on:
unexpected movement, lost/stale scan, localization discontinuity, broken TF,
planner/controller mismatch, dangerous minimum clearance, controller
oscillation, radio loss, failed cancellation, loss of operator visibility,
or any safety-device problem.

## G. Evidence grading and publication rule

- A verified `rosbag` alone does not prove C01 was the selected planner:
  cross-check planning traces and adapter/launch configuration.
- A successful Nav2 simulation does not prove physical efficacy.
- A route calculated using a physical map is still offline evidence.
- C01 only receives `PHYSICAL_ROBOT_VALIDATED` after reviewing actual
  synchronized physical motion, selected planner execution, raw artifacts,
  hardware controls, trial validity and outcomes.
- Do not insert C01 hardware claims into the current DynNav-R paper without
  an explicit scientific rationale and new frozen evidence contract. The
  paper's main contribution is history-conditioned action-triggered
  return-connectivity, not generic learned A* speedup.

**Status today:** Protocol prepared. No physical C01 trials completed or
claimed.
