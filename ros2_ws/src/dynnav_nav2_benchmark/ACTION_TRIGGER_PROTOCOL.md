# Action-trigger observation protocol

The action-triggered Gazebo benchmark treats execution history as observed data, not inferred path geometry.

A trigger is credited only when two consecutive robot observations quantize to the configured directed adjacent grid cells. Repeated observations in the same cell do not create transitions. If consecutive observations skip one or more grid cells, the interval is always retained as a sampling gap and the benchmark never interpolates or invents a missing transition. For the single-hazard protocol, a trial is invalidated by a gap only when the configured directed trigger lies on a minimum-length 4-connected connection between the two observed cells, because only then can the gap make the activation label ambiguous. Remote diagonal or skipped-cell observations remain audit data but do not erase an otherwise unambiguous trigger label.

The first frozen scenario uses directed trigger `(174,189) -> (175,189)` and closure cell `(181,191)`, selected from a retained pre-outcome Gazebo execution trace. The closure probability is 0.8. Comparative outcomes must not be used to move this trigger without a protocol version change.

A stochastic closure is sampled once per repetition and hazard identifier and reused across planners. The physical blocker is requested only if the trigger was actually observed for that planner and the paired latent event realizes closure. Because the modeled event is a \emph{future} closure, physical injection is delayed until the robot is at least the frozen minimum-clearance distance from the blocker location; the clearance threshold is never relaxed to make a trial valid. If the robot never reaches safe injection clearance, the trial is explicitly invalid. Planner history state is updated from executed transitions only; a planned path never activates a hazard.

Primary trial fields are navigation success, trigger observed, closure realized/applied, blocker observed in the global costmap, recovery feasible, and operational irreversible failure. Invalid observation/injection trials are reported separately rather than converted to mission failures.


## September 2026 validity revision

A pre-publication audit exposed two over-strict/incorrect implementation behaviors before any Gazebo efficacy result was admitted to the paper:

1. any sampling gap anywhere on the route invalidated the trial, even when it could not conceal the configured trigger;
2. a realized closure was rejected immediately when the robot was still inside the minimum blocker-clearance radius, rather than remaining pending as a future closure.

The revised implementation preserves all sampling gaps, invalidates only trigger-ambiguous gaps, and keeps a realized closure pending until the unchanged clearance gate is satisfied. These changes alter validation/execution semantics, not the trigger, closure probability, blocker size, or minimum-clearance threshold. Publication-facing Gazebo results must come from a retained artifact generated after this revision.


## V4 partial-observation extension

V4 introduces a latent environmental arming state between observed trigger
execution and future closure realization. This changes the causal semantics from

```text
observed trigger -> closure draw
```

to

```text
known executed trigger
    -> hidden arming draw
    -> noisy detector observation delivered to non-oracle planner
    -> later closure draw conditional on true arming
```

The benchmark controller owns the latent `true_armed` state. A non-oracle
planner must never receive that value or the future closure realization. Its
planner-facing message may contain only:

- hazard identifier;
- noisy `observed_armed` detector outcome;
- declared arming probability;
- declared detector sensitivity/specificity;
- declared conditional closure probability.

The explicit oracle condition is the only condition permitted to receive the
latent arming truth.

The ROS-independent contract is implemented in
`dynnav_nav2_benchmark/v4_hidden_arming.py` so this information barrier can be
tested without relying on Gazebo topic conventions.

### Required execution logging

For audit and post-hoc scoring, the benchmark artifact must retain both sides of
the information barrier:

- executed trigger transition;
- latent arming draw and true arming state;
- detector draw and planner-visible detector outcome;
- planner condition;
- posterior/belief state if applicable;
- future closure draw and physical blocker application;
- recovery assessment.

Truth fields are evaluator data. Their presence in the retained artifact does
not authorize exposing them to a non-oracle planner at runtime.

### Validity rule

Any trial in which a non-oracle planner can read latent arming truth or future
closure truth is protocol-invalid. A truth-leakage bug invalidates the affected
comparative run and requires a complete rerun of the frozen condition after the
bug is fixed.
