# G1 Gazebo V2 Protocol — Canonical Parallel-Return Dependence

**Freeze date:** 2026-09-25  
**Status:** pre-outcome protocol. No execution result from this canonical world had been inspected when this file was created.

## Why V2 exists

The retained TurtleBot3 sandbox was commissioned first using only pre-existing costmap evidence. The deterministic commissioning search found no second blocker with nonzero two-hazard return-connectivity interaction, so the sandbox is rejected for the G1 dependence experiment. No post-hoc blocker search is permitted in that map.

V2 therefore instantiates the already-frozen analytic G1 parallel-corridor construction directly in Gazebo/Nav2 rather than tuning the legacy sandbox.

## Canonical environment

Map resolution: **0.05 m/cell**. World footprint: **7.0 m × 5.0 m** with 0.15 m outer walls.

Central static island: x=1.5..5.5 m, y=1.7..3.3 m. This creates two parallel return corridors.

Start/safe center: `(0.775, 0.925)` m, radius `0.35 m`. Goal: `(6.275, 0.925)` m.

## Action-triggered hazards

Both hazards have marginal closure probability `p=0.5`.

- Hazard 0 trigger: `(4.675,0.925) -> (4.725,0.925)` m; physical closure: bottom return corridor at x=1.25 m.
- Hazard 1 trigger: `(4.725,0.925) -> (4.775,0.925)` m; physical closure: top return corridor at x=1.25 m.

Each blocker is `0.35 × 1.55 × 1.0 m`. The planner receives every costmap cell covered by that same physical footprint; V2 does not use single-cell closure modeling.

## Topological mechanism

The target deterministic truth table is `(f00,f10,f01,f11)=(1,1,1,0)`, giving `kappa=-1`: either single closure remains returnable, but the joint closure disconnects return.

## Planner conditions

- `DynNavShortest`: no history-aware return penalty.
- `DynNavHistory`: activated-history semantics with independent future closures.
- `DynNavRobustHistory`: activated-history semantics with `q=P(C0=1,C1=1)` allowed in `[0,0.5]`.

Recoverability weight is frozen at **12.0**, inherited from the pre-outcome synthetic G1 route-choice construction.

## Pre-outcome route calculation

At 5 cm resolution the direct bottom route is about 110 transitions; the second trigger is about 30 cells before the goal. After both hazards activate, independence gives `R=0.75` and a per-step penalty of `3`, while arbitrary-dependence worst-case gives `R=0.50` and a per-step penalty of `6`. The top detour is about 244 transitions.

Therefore the pre-outcome model predicts approximately: independence direct `200`, robust direct `290`, trigger-free detour `244`. The intended ordering is `DynNavHistory: direct < detour` and `DynNavRobustHistory: detour < direct`.

## Dependence conditions

Latent closure draws are paired across planners within each repetition. Three fixed conditions preserve `p=0.5` marginals: `independent`, `common_cause`, and `anti_correlated` (exactly one closes). Planner choice does not affect latent draws.

## Trial reset semantics

Before every trial the runner publishes `__RESET__`. Each history-aware planner clears its activated hazard mask and last observed executed cell. Both blockers are parked and the robot is reset before planning.

## PR smoke gate

The pull-request workflow runs **1 repetition per dependence condition**, giving 9 planner trials. This tests startup, plugin loading, blocker reset/injection, executed-transition observation, paired latent outcomes, recovery assessment, and artifact validity. A smoke outcome is not confirmatory efficacy evidence.

## Confirmatory target

After a valid smoke gate, the retained confirmatory target is **10 paired repetitions per dependence condition**: 3 dependence conditions × 3 planners × 10 repetitions = **90 valid trials**. Invalid trials are reported and never silently reclassified.

## Primary outcomes

Trigger-0/trigger-1 observation, both-trigger activation, closures applied, navigation success, operational irreversible failure, recovery feasibility, and navigation time where available. The primary mechanism outcome is route/trigger exposure, not success alone.

## Frozen hypotheses

- **G1-GZ-H1:** `DynNavHistory` executes both direct-route triggers more often than `DynNavRobustHistory`.
- **G1-GZ-H2:** under common-cause truth, activating both hazards exposes independence-history planning to greater irreversible-return risk because robust-history is designed to avoid the two-trigger route.
- **G1-GZ-H3:** under anti-correlated truth, arbitrary-dependence robustness can be unnecessarily conservative; extra travel/time is retained as a negative-control cost.
- **G1-GZ-H4:** `DynNavShortest` favors the geometric direct route and provides a no-return-reasoning exposure baseline.

## Claim boundary

Even a successful V2 study is controlled Gazebo/Nav2 mechanism evidence, not a universal robot-safety or physical-robot guarantee.
