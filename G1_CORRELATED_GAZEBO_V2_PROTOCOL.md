# G1 Correlated Gazebo V2 Protocol

**Status:** frozen before any v2 Gazebo planner outcomes.

## Why a new environment is required

The retained TurtleBot3 sandbox was commissioned against the predeclared two-hazard dependence-interaction criterion. The retained commissioning artifact found zero second-blocker candidates with nonzero connectivity interaction. That environment is therefore rejected for correlated G1 execution validation and is not retuned post hoc.

V2 instantiates the already-defined analytic G1 parallel-corridor construction directly in Gazebo/Nav2.

## Frozen environment

- map: `maps/g1_parallel_corridor.yaml`;
- Gazebo world: `worlds/g1_parallel_corridor.sdf.xacro`;
- physical blocker: `models/g1_parallel_corridor_blocker.sdf`;
- scenario: `config/sandbox_correlated_history_events.yaml`;
- occupancy resolution: 0.05 m;
- start / safe-region center: `(0.8, 4.075)`;
- goal: `(6.2, 4.075)`;
- central static island: 4.0 m × 1.6 m;
- two dynamic blocker footprints: 0.40 m × 1.55 m.

The machine-checkable topology contract must satisfy

`(f00, f10, f01, f11) = (1, 1, 1, 0)`

and therefore

`kappa = f00 - f10 - f01 + f11 = -1`.

No Gazebo trial may be interpreted if this contract fails.

## Frozen action-trigger hazards

Both hazards have marginal closure probability 0.5.

1. Top return gate:
   - trigger grid transition `(72,81) -> (73,81)`;
   - world trigger `(3.625,4.075) -> (3.675,4.075)`;
   - blocker center `(1.8,4.075)`.
2. Bottom return gate:
   - trigger grid transition `(92,81) -> (93,81)`;
   - world trigger `(4.625,4.075) -> (4.675,4.075)`;
   - blocker center `(1.8,0.925)`.

Planner history is activated only by observed executed directed transitions. A blocker is physically injected only when its corresponding trigger is observed and that hazard's paired latent outcome realizes closure.

## Dependence conditions

The paired latent truth conditions are frozen as:

- `independent`: independent Bernoulli(0.5) closures;
- `common_cause`: both closures share one Bernoulli(0.5) latent event;
- `anti_correlated`: exactly one closure realizes, preserving 0.5 marginals.

The same repetition-level latent outcomes are shared across planner conditions.

## Planner conditions

- `DynNavShortest`: geometry-only DynNav planner;
- `DynNavHistory`: executed-history planner using independent closure multiplication;
- `DynNavRobustHistory`: executed-history planner minimizing return probability over the feasible pairwise joint interval `q in [0, 0.5]`.

The robust and independence planners use the same triggers, physical closure footprints, marginal probabilities, safe region and recoverability weight. They differ only in the dependence model.

## Frozen planning parameters

- recoverability weight: 12.0;
- maximum modeled hazards: 2;
- robust pairwise joint interval: `[0.0, 0.5]`;
- physical closure footprints are rasterized into all covered planning cells.

The second trigger is frozen 31 map cells before the goal. On the uninflated canonical map, the direct path is approximately 108 cells and the trigger-free detour approximately 234 cells. With weight 12, the analytic history objective gives a broad route-choice margin: independence remains below the detour cost, while arbitrary-dependence robustness exceeds it. This calculation was made before v2 Gazebo outcomes.

## Primary outcomes

For each dependence condition and planner:

- valid-trial rate;
- trigger-observation rate for each hazard;
- closure-application rate for each hazard;
- navigation success;
- recovery feasibility after execution;
- operational irreversible failure;
- accepted executed-transition trace;
- sampling-gap incidence.

Secondary outcomes include navigation duration and planner path information when available.

## Frozen hypotheses

- **V2-H1:** `DynNavShortest` and `DynNavHistory` preferentially use the direct top corridor in the no-outcome planning model.
- **V2-H2:** `DynNavRobustHistory` preferentially uses the trigger-free detour because the worst-case common-cause-compatible joint closure makes the direct corridor less attractive.
- **V2-H3:** under common-cause truth, direct-route planners have higher exposure to jointly applied closures than the robust planner.
- **V2-H4:** under anti-correlated truth, at most one physical return gate closes per repetition; this is a negative control for joint-disconnection failure.
- **V2-H5:** any sampling-gap or unsafe-injection-clearance trial is invalid rather than repaired or interpolated.

## Stop and integrity rules

- No trigger, blocker pose, corridor geometry, dependence distribution, weight, or timeout may be changed after the first v2 Gazebo outcome is inspected without a protocol version change.
- A failed topology contract blocks execution.
- A failed ROS build/test blocks execution.
- Invalid trials are retained and reported; they are not silently replaced.
- This experiment provides simulation evidence only. It is not a physical-robot safety certificate.
