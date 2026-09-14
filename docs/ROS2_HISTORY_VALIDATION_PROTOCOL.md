# Frozen ROS 2 / Gazebo history-conditioned validation protocol

Status: **protocol frozen before outcome inspection**.

This protocol defines the first execution-level test of the history-conditioned safe-return representation. It does not change the paper claim until retained ROS 2 / Gazebo artifacts exist.

## Question

When an executed robot transition activates a future topology-closure hazard, does retaining the activated-hazard history change the route selected by an online planner and the resulting post-event return feasibility in the existing Nav2 / Gazebo route-invalidation harness?

## Planner conditions

The first retained comparison will include, at minimum:

1. `nav2_shortest`: a geometry/costmap-driven Nav2 reference without trigger-history state;
2. `dynnav_state_only`: the existing DynNav Nav2 planner using its current cost/risk/irreversibility representation but no action-triggered hazard memory;
3. `dynnav_history`: the history-conditioned mode carrying activated trigger IDs across replans.

The experiment is about the representation. It is **not** predeclared as a soft-objective superiority test; a hard safe-return condition may be added as a strong baseline if it can be integrated without changing the frozen scenarios.

## Event semantics

A scenario contains a directed trigger transition and a corresponding future closure/blocker pose. The closure event is eligible only after the robot has actually traversed the trigger. Event realization is indexed by `(scenario, repetition, hazard_id)` and uses the same latent draw for all planner conditions (common random numbers). A planner that never activates a hazard does not realize that event, but the latent draw still exists for pairing.

The existing Gazebo blocker model and `SetEntityPose` injection mechanism are reused. The blocker must be observed in the global costmap before a trial is considered valid.

## Frozen validity requirements

A retained trial is valid only if all applicable checks pass:

- the robot reset pose is within the existing reset tolerance;
- a pre-event planner path was observed;
- the declared trigger was crossed before event eligibility;
- the injected blocker is observed in the global costmap;
- the event geometry closes the declared return connection or route region;
- a post-event costmap snapshot is retained;
- recovery reachability can be assessed from the post-event robot pose.

Infrastructure-invalid trials are reported separately and never counted as navigation successes or failures.

## Outcomes

Primary binary outcomes:

- `navigation_success`;
- `recovery_feasible` after event realization;
- `irreversible_failure`, defined as mission/navigation failure **and** no reachable designated safe region under the retained post-event costmap assessment.

Representation/process outcomes:

- trigger crossed;
- activated hazard IDs at every replan;
- event realized/not realized;
- number of replans;
- route/path trace before and after activation;
- post-event blocker observation.

Continuous diagnostics:

- path length;
- navigation time;
- planning/replanning latency where instrumentation permits;
- minimum reported return reliability for the history-conditioned planner;
- recovery path length/budget margin.

Undefined continuous quantities on failed/invalid trials are never silently dropped; finite and excluded counts are retained.

## Pairing and seeds

Planner conditions use the same frozen scenario order and event-index random draws. Binary comparisons are paired by `(scenario, repetition)`. If enough valid paired trials exist, risk differences, paired bootstrap intervals, and exact McNemar tests will be reported. No significance threshold is used to redefine or discard scenarios.

## Scenario policy

The first scenarios must be selected from the existing route-invalidation world(s) before inspecting comparative outcomes. Geometry may be changed only to repair a documented infrastructure invalidity (for example blocker not visible in costmap or trigger outside traversable space); such a change requires a new protocol version and new retained run.

## Claim boundary

A successful result supports **ROS 2 / Gazebo simulation validation** of the history-conditioned representation under the tested dynamic topology events. It does not establish hardware validation, collision/kinodynamic safety, arbitrary-map generalization, calibrated real-world closure probabilities, or universal superiority over hard safe-return planners.
