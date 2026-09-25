# G1 Gazebo V4 Protocol — Localization-Controlled Execution

**Freeze date:** 2026-09-25  
**Status:** pre-outcome protocol. Created after the completed V3.1 confirmatory execution-validity failure and before any V4 Gazebo outcome.

## Motivation and retained failed predecessor

V3.1 fixed the global planning cost surface and reproduced the frozen planner-route mechanism on every attempted trial, but all three 10-repetition dependence slices failed the preregistered execution-validity gate because AMCL produced multi-metre localization jumps.

Retained V3.1 verdict:

- independent: route audit passed; History↔Robust paired-valid = 6/10;
- common-cause: route audit passed; History↔Robust paired-valid = 6/10;
- anti-correlated: route audit passed; History↔Robust paired-valid = 7/10;
- required minimum: 8/10 in every slice.

Those artifacts remain diagnostic evidence and are excluded from confirmatory execution-efficacy claims.

## Frozen mechanism

V4 does **not** change:

- occupancy map pixels or map resolution;
- canonical world geometry;
- start, goal, or safe region;
- the two full-corridor trigger gates;
- physical blocker poses or footprints;
- marginal closure probability (0.5 for each hazard);
- dependence conditions (independent, common_cause, anti_correlated);
- recoverability weight (12.0);
- pairwise ambiguity interval q in [0,0.5];
- planner plugins or objectives;
- static-map-only global planning costmap;
- sensor-driven local costmap;
- recovery oracle semantics;
- trial validity thresholds;
- paired latent-outcome construction.

The machine-checkable topology contract remains `(f00,f10,f01,f11)=(1,1,1,0)` with `kappa=-1`.

The exact frozen route audit remains:

- DynNavShortest: direct route, both trigger gates;
- DynNavHistory: direct route, both trigger gates;
- DynNavRobustHistory: lower trigger-free detour.

## V4 localization intervention

V4 disables AMCL and retains the static map server.

A dedicated resettable odometry-localization node publishes `map -> odom`.

Let the current odometry pose be `T_odom_base` and the frozen start pose be `T_map_start`. On the reserved trial reset command `__RESET__`, the node sets

`T_map_odom = T_map_start * inverse(T_odom_base)`.

Therefore the current robot pose is aligned exactly with the frozen map start after every Gazebo teleport even if the differential-drive odometry itself is not reset.

The transform is then propagated with every `/odom` update. This uses simulator wheel odometry as the localization source and removes scan-matching ambiguity from the execution study.

### What remains sensor-driven

The local Nav2 costmap remains unchanged and consumes the simulated range sensor. Physical blockers are therefore still observed by the controller/collision layer. V4 is not a kinematic path replay.

The global planner continues to use the frozen static-map-plus-inflation costmap introduced in V3.1, so initial route choice is not affected by prior scan history.

## Trial lifecycle

For every planner trial:

1. both blockers are parked;
2. the Gazebo robot is teleported to the frozen start;
3. costmaps are cleared;
4. the runner publishes `__RESET__`;
5. the history-aware planners clear activated hazard state;
6. the odometry localizer re-anchors `map -> odom` using the latest `/odom`;
7. the mandatory initial ComputePathToPose audit is recorded;
8. navigation executes with the unchanged controller/local sensor costmap;
9. trigger crossings activate paired latent closure outcomes;
10. realized blockers are injected only after their observed trigger;
11. recovery is evaluated on the static global map with actually applied blocker footprints overlaid as lethal cells.

## V4 smoke gate

Before any V4 confirmatory run:

- 1 paired repetition per dependence condition;
- 3 planners per repetition;
- 9 attempted trials total.

The smoke passes only if:

- topology contract passes;
- ROS/C++/Python tests pass;
- all nine initial route audits match the frozen route expectation;
- all nine trials are valid;
- no trial is invalidated by localization jump, sampling gap, unsafe injection clearance, or insufficient motion.

Smoke outcomes are commissioning evidence only.

## V4 confirmatory target

After a successful smoke:

- 10 paired repetitions per dependence condition;
- 3 dependence conditions;
- 3 planners;
- 90 attempted trials;
- minimum paired-valid DynNavHistory↔DynNavRobustHistory: **8/10 per dependence slice**, unchanged from V3.1.

Invalid trials remain retained and are never replaced or silently re-run to fill the denominator.

## Primary hypotheses

- **V4-H1 planning mechanism:** initial route audit remains invariant: History/Shortest direct with both gates; Robust trigger-free detour.
- **V4-H2 exposure:** Robust has lower both-trigger exposure than History in each dependence slice.
- **V4-H3 common-cause:** under common-cause truth, the robust detour reduces realized joint-return-cut exposure relative to History.
- **V4-H4 anti-correlated harm/control:** under anti-correlation, robust planning pays route/time cost even though the two hazards cannot jointly close.
- **V4-H5 execution validity:** localization-controlled execution meets the unchanged >=8/10 paired-valid gate in each slice.

## Claim boundary

V4 deliberately removes a localization estimator from the causal path of the experiment. A successful V4 therefore supports a **planning-and-execution mechanism under controlled simulator localization**, not robustness to localization uncertainty and not a physical-robot safety guarantee.

Any future AMCL or hardware claim requires a separate protocol.
