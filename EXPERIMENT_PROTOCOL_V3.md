# Experiment Protocol V3

## Scope

V3 is the current publication-facing protocol for **history-conditioned safe-return planning under action-triggered topology hazards**. It supersedes the earlier J0–J3 factorial protocol for current-paper claims; that protocol is retained in `docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md`.

The core question is whether executed path history carries recoverability-relevant information that a state-only marginal future-risk model discards when robot actions activate future closure hazards.

## Frozen semantics

A hazard is defined by:

- a directed trigger transition `(source_cell -> target_cell)`;
- a closure cell or closure event;
- a declared activation-conditioned closure probability;
- an identifier used to pair latent stochastic draws across planner conditions.

Persistent hazard history is updated only from **executed transitions**. A nominal or candidate plan may reason about future activations, but it never mutates the persistent history state.

Two trajectories may end at the same geometric cell while carrying different activated-hazard histories. This is the representation difference under test.

## Primary planners and baselines

Publication-facing comparisons should include the smallest set needed for the question:

1. geometric shortest / NavFn reference where appropriate;
2. state-only marginal return-risk baseline;
3. exact history-aware augmented-state planner;
4. critical-cut history approximation when scaling is studied;
5. hard safe-return threshold baseline when objective-form comparison is studied.

Do not omit a strong baseline because it performs well. The geometric Pareto evidence already shows that hard safe-return constraints can match the safe route in some frozen worlds.

## Evidence families

### A. Information mechanism

Use same-endpoint histories that differ only in whether an action trigger was traversed. Report exact history-conditioned return probability and the state-only marginal estimate. This establishes representation aliasing, not deployment efficacy.

### B. Decision mechanism

Use controlled commitment scenarios and analytic route-switch constructions. Confirm expected switch boundaries and retain both positive and no-effect regions.

### C. Stochastic execution

Use common random numbers: generate one latent draw per declared hazard/event index and reuse it across planner conditions. A closure is applied only when that planner actually activated the corresponding hazard.

### D. Held-out generalization

Freeze scenario topology/probability families before inspecting outcomes. Existing retained studies include probability/horizon held-outs and the fork/L-room/chamber geometric held-outs.

### E. Approximation boundary

Evaluate both a regime where the critical-cut approximation is exact by construction and an adversarial joint-cut regime where individually noncritical hazards can jointly disconnect return connectivity.

### F. Objective-form sensitivity

Compare soft history penalties with hard safe-return thresholds over a predeclared grid. Report Pareto/risk-cost behavior rather than choosing one tuned point after outcomes.

## Frozen action-triggered Gazebo protocol

The first execution-level scenario was selected from a retained pre-outcome Gazebo trace.

- directed trigger: `(174,189) -> (175,189)`;
- closure cell: `(181,191)`;
- declared closure probability: `0.8`;
- comparison set: `NavFn`, `DynNavShortest`, `DynNavHistory`.

This geometry/probability must not be moved after comparative outcomes without a protocol-version change.

### Executed-transition observation rule

A trigger is credited only when consecutive robot observations quantize to the configured directed **adjacent** cells.

- repeated samples in the same cell do not create a transition;
- sampling gaps that skip one or more cells are invalid observation intervals;
- the runner must not interpolate or invent missing executed transitions;
- planned paths never count as trigger observations.

### Paired event realization

For each `(scenario, repetition, hazard_id)`, generate a deterministic latent draw and reuse it across planners. The physical closure is injected only if:

1. the planner actually traversed the frozen trigger; and
2. the paired latent draw realizes the declared event.

### Validity checks

A Gazebo trial is valid for efficacy analysis only when all required protocol conditions are observed and logged:

- navigation stack reaches the required lifecycle state;
- start/reset is within frozen tolerance;
- trigger observation is valid under the adjacent-transition rule;
- closure injection succeeds when required;
- injected blocker becomes visible in the relevant global costmap within the observation window;
- recovery assessment can be computed from a valid post-event state.

Protocol-invalid trials are reported separately. They are not silently converted to mission failures and are not dropped without an explicit reason.

## Outcomes

Primary execution-level outcome:

`post_invalidation_recovery_infeasible_failure = mission_failure AND recovery_feasible == false`

Report `mission_success` and `recovery_feasible` separately so ordinary mission failure is not conflated with irrecoverability.

Secondary outcomes may include:

- path/executed-path length;
- navigation duration;
- planning/replanning latency;
- activated-hazard count;
- exact model return probability where defined;
- replan count;
- blocker/costmap observation diagnostics;
- invalid-trial reason.

## Statistical rules

- Preserve planner pairing by scenario/seed/event index.
- Failed mission trials remain in binary-outcome denominators when protocol-valid.
- Continuous metrics exclude non-finite observations only with explicit finite-count/exclusion reporting.
- Use paired risk differences and bootstrap confidence intervals for binary-rate contrasts; exact McNemar tests are appropriate for paired binary outcomes.
- Use equivalence/non-inferiority procedures only with margins frozen before outcome inspection.
- Do not treat multiple planners run on the same stochastic world as independent samples.

## Timing integrity

Planning latency must include all computation required by the compared planner mode, including recoverability/history-map/oracle construction that occurs as part of the decision. Post-hoc diagnostics that are not required for planning should be reported separately rather than charged selectively to one method.

## Artifact contract

Each retained publication-facing run should record:

- exact Git SHA and dirty state;
- workflow/run ID and artifact ID/digest when executed in CI;
- command/configuration and seed policy;
- planner parameters and baseline identity;
- scenario/world/map/event specification;
- raw per-trial CSV/JSON;
- validity and exclusion reasons;
- summary/statistical output generated from the raw trials;
- environment/package versions needed for reproduction.

ROS/Gazebo execution evidence should additionally retain relevant logs, costmap snapshots and rosbag metadata/bags where feasible.

Every manuscript number should be traceable through `paper/dynnav_r/evidence_manifest.json`.

## Claim discipline

V3 does not authorize claims of:

- formal safety or certification;
- calibrated real-world closure probabilities;
- universal superiority over hard safe-return constraints;
- universal exactness of the critical-cut approximation;
- physical-robot efficacy;
- broad real-world generalization.

New claims require a frozen protocol, valid retained artifact and an explicit limitation/failure boundary.
