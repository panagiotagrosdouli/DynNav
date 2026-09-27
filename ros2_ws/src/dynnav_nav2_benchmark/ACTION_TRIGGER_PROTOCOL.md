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
