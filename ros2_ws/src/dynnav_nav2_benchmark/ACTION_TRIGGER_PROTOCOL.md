# Action-trigger observation protocol

The action-triggered Gazebo benchmark treats execution history as observed data, not inferred path geometry.

A trigger is credited only when two consecutive robot observations quantize to the configured directed adjacent grid cells. Repeated observations in the same cell do not create transitions. If consecutive observations skip one or more grid cells, the interval is recorded as a sampling gap and the benchmark does not interpolate or invent the missing transitions.

The first frozen scenario uses directed trigger `(174,189) -> (175,189)` and closure cell `(181,191)`, selected from a retained pre-outcome Gazebo execution trace. The closure probability is 0.8. Comparative outcomes must not be used to move this trigger without a protocol version change.

A stochastic closure is sampled once per repetition and hazard identifier and reused across planners. The physical blocker is moved only if the trigger was actually observed for that planner and the paired latent event realizes closure. Planner history state is updated from executed transitions only; a planned path never activates a hazard.

Primary trial fields are navigation success, trigger observed, closure realized/applied, blocker observed in the global costmap, recovery feasible, and operational irreversible failure. Invalid observation/injection trials are reported separately rather than converted to mission failures.
