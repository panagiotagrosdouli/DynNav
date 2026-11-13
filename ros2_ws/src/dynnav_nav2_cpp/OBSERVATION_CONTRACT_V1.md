# Executed-transition observation contract v1

This revision strengthens observation validity; historical unversioned trial
artifacts remain unchanged. Trigger coordinates, closure probabilities and
planner objective parameters are not changed. New benchmark outputs identify
`execution_observation_contract: stamped_v1` and must not be relabeled as the
original observation protocol.

The String topic `dynnav/executed_transition` now requires:

```
v1|map|measurement_stamp_ns|sx:sy>tx:ty
```

The frame must exactly match the configured global costmap frame. The stamp is
the TF measurement stamp in the same ROS clock domain as the planner, not the
subscriber's reception time. Zero, repeated/out-of-order, older-than-1.5-second,
or more-than-50-millisecond-future events are rejected. Integer fields contain
ASCII digits only, are range checked, and must consume their entire token.
Only adjacent directed transitions are accepted. Old unframed messages are
rejected rather than silently promoted to observed evidence.

The benchmark publishes the actual TF stamp, ignores repeated transforms, and
marks trials with invalid frame/stamp observations invalid. It never connects
across an invalid observation by interpolating missing motion.

The geometry and cost bytes are copied under one costmap lock. Returned world
coordinates use that immutable geometry snapshot. A history-aware map's cell
layout must match its configuration (dimensions, origin, resolution); a changed
layout requires explicit lifecycle reconfiguration. Replanning and invalid
messages never clear activated history. `dynnav/reset_history` is still an
explicit trusted mission-reset command; it is not an authenticated interface.

These checks establish message consistency, not sensor authenticity, physical
motion truth or certified safety. The String transport is retained for migration;
a typed observation message and authenticated publisher remain future work.
