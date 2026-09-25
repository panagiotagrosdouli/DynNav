# G1 Correlated Gazebo V3 Protocol

**Status:** V2.3 computational-validity amendment after two invalid integration smokes and before any valid comparative planner outcome.

## Why a new environment is required

The retained TurtleBot3 sandbox was commissioned against the predeclared two-hazard dependence-interaction criterion. The retained commissioning artifact found zero second-blocker candidates with nonzero connectivity interaction. That environment is therefore rejected for correlated G1 execution validation and is not retuned post hoc.

V2 instantiates the already-defined analytic G1 parallel-corridor construction directly in Gazebo/Nav2.

### V2.2 validity amendment

The first V2 smoke completed the software path but all nine trials remained at the start and timed out because the simulator initially spawned the robot at `(0,0)` while the original canonical map occupied only positive coordinates. That smoke is retained as invalid integration evidence and is not used as an efficacy result. V2.2 applies one rigid translation to the map origin, Gazebo world and all scenario poses so that `(0,0)` is the frozen start pose. The occupancy pixels, grid-cell topology, trigger cells, blocker footprints, marginal probabilities, dependence conditions and recoverability weight are unchanged. The machine-checkable topology contract must remain identical after translation.

### V3 full-corridor trigger-gate correction

A static audit of the frozen V2.x occupancy map found that the 0.75 m trigger-gate half-width did **not** span the complete 2.0 m top corridor. Both history planners could therefore avoid trigger activation through a short local bypass around the gate, which violates the intended analytic construction where avoiding the two direct-route triggers requires taking the lower return corridor.

V3 changes only the trigger-gate half-width from **0.75 m to 1.0 m** for both hazards. The trigger x-locations, map pixels, world geometry, blocker footprints, closure probabilities, dependence conditions, safe region and recoverability weight are unchanged.

The correction is derived entirely from the static map geometry. At each trigger boundary, 1.0 m half-width covers the full free top-corridor edge set. On the raw 5 cm occupancy graph with the frozen weight 12, the pre-outcome augmented-state calculation is:

- independence-history: direct route, 108 transitions, both triggers active, objective cost 204;
- arbitrary-dependence robust-history: lower trigger-free detour, 230 transitions, objective cost 230.

The V2.x execution outcomes are not used to tune these values and are not included in V3 efficacy denominators.

### V2.3 planner-route diagnostic amendment

V2.2 demonstrated that the robot can physically traverse the canonical world, but execution outcomes were partly contaminated by controller replanning failures and one localization jump. Before any further execution-level interpretation, V2.3 records a direct `ComputePathToPose` query for the frozen start and goal immediately after the history reset and before robot motion. For each planner it retains path length, path cells, route class, and whether the path crosses each frozen trigger gate.

This diagnostic does not alter the executed navigation goal or any planner parameter. It separates the planner mechanism claim from localization/controller behavior. The preregistered planning mechanism is supported only if the initial plan itself shows the expected direct-versus-detour distinction.

Before any admissible V2.2 outcome, this document was also synchronized with the already-committed V2.1 canonical assets: the island is `4.0 × 2.0 m`, the blocker footprint is `0.40 × 2.05 m`, and the trigger grid row is `104`. These are documentation corrections only; the underlying committed assets and machine-checkable topology contract are unchanged.

### V2.3 computational-validity amendment

The translated V2.2 smoke preserved the required topology contract exactly, but it was still invalid: the first history-aware planning request remained inside `compute_path_to_pose` until the 75 s execution timeout, so the robot never moved. The direct cause was computational rather than geometric: the exact history search recomputed full-grid safe-return reachability separately for nearly every augmented state. After the first timeout, `BasicNavigator` also retained the previous feedback object, so subsequent trials could observe a stale 75 s `navigation_time` and cancel immediately.

V2.3 changes only execution efficiency and trial isolation:

1. closure-scenario reachability is cached exactly inside one planning call; with two hazards, at most four closure-realization connectivity maps are computed and all state-wise return probabilities are exact lookups;
2. the public direct return-probability oracles remain unchanged and continue to serve as reference implementations/tests;
3. `navigator.feedback` is explicitly cleared before each new trial so stale timeout feedback cannot affect the next planner condition.

No map cell, world geometry, trigger gate, blocker footprint, closure probability, dependence condition, recoverability weight, safe region, planner objective or timeout is changed. Because no V2/V2.2 trial produced a valid comparative execution, this amendment occurs before any admissible planner outcome.

## Frozen environment

- map: `maps/g1_parallel_corridor.yaml`;
- Gazebo world: `worlds/g1_parallel_corridor.sdf.xacro`;
- map origin: `(-0.8, -5.225)` m;
- physical blocker: `models/g1_parallel_corridor_blocker.sdf`;
- scenario: `config/sandbox_correlated_history_events.yaml`;
- occupancy resolution: 0.05 m;
- start / safe-region center: `(0.0, 0.0)`;
- goal: `(5.4, 0.0)`;
- central static island: 4.0 m × 2.0 m;
- two dynamic blocker footprints: 0.40 m × 2.05 m.

The machine-checkable topology contract must satisfy

`(f00, f10, f01, f11) = (1, 1, 1, 0)`

and therefore

`kappa = f00 - f10 - f01 + f11 = -1`.

No Gazebo trial may be interpreted if this contract fails.

## Frozen action-trigger hazards

Both hazards have marginal closure probability 0.5.

1. Top return gate:
   - trigger grid transition `(72,104) -> (73,104)`;
   - world trigger `(2.825,0.0) -> (2.875,0.0)`;
   - blocker center `(1.0,0.0)`.
2. Bottom return gate:
   - trigger grid transition `(92,104) -> (93,104)`;
   - world trigger `(3.825,0.0) -> (3.875,0.0)`;
   - blocker center `(1.0,-4.05)`.

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

The second trigger location is unchanged. Under the corrected full-corridor gates on the uninflated canonical map, the direct route is 108 transitions and the trigger-free lower detour is 230 transitions. With weight 12, the exact augmented-state calculation gives independence-history cost 204 on the direct route and robust-history cost 230 on the detour. This V3 calculation is a static graph check made before any V3 Gazebo outcome.

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

Secondary outcomes include navigation duration. V2.3 additionally records a mandatory pre-execution planner-server path audit: planning success, path length, route class, trigger-gate crossings and rasterized path cells.

## Frozen hypotheses

- **V2-H1:** `DynNavShortest` and `DynNavHistory` preferentially use the direct top corridor in the no-outcome planning model.
- **V2-H2:** `DynNavRobustHistory` preferentially uses the trigger-free detour because the worst-case common-cause-compatible joint closure makes the direct corridor less attractive.
- **V2-H3:** under common-cause truth, direct-route planners have higher exposure to jointly applied closures than the robust planner.
- **V2-H4:** under anti-correlated truth, at most one physical return gate closes per repetition; this is a negative control for joint-disconnection failure.
- **V2-H5:** any sampling-gap, unsafe-injection-clearance, localization-jump, or no-motion trial is invalid rather than repaired or interpolated.

## Stop and integrity rules

- No trigger, blocker relative pose, corridor geometry, dependence distribution, weight, or timeout may be changed after the first valid V2.3 Gazebo outcome is inspected without a protocol version change. The V2.2 rigid translation and V2.3 exact-connectivity caching/trial-feedback reset are the only pre-valid-outcome amendments and are documented above.
- A failed topology contract blocks execution.
- A failed ROS build/test blocks execution.
- Invalid trials are retained and reported; they are not silently replaced.
- This experiment provides simulation evidence only. It is not a physical-robot safety certificate.
