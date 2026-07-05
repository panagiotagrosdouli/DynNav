# Dynamic SelfAwareAStar Replanning Benchmark

This benchmark evaluates online replanning when the environment changes during execution.

## Research question

Can risk-aware self-aware replanning reduce unsafe execution compared with classical A* replanning when new obstacles and risk spikes appear online?

## Compared methods

| Method | Description |
|---|---|
| `classic_astar` | Replans with unit-cost A* when the current route becomes blocked or unsafe. |
| `dynamic_self_aware_astar` | Replans with SelfAwareAStar using risk, uncertainty, recoverability, and information-gain terms. |

## Dynamic events

During execution, the benchmark can introduce:

- new blocked cells near the robot,
- sudden risk spikes near the current route,
- higher uncertainty around risk-spike cells.

The robot replans from its current cell when the next step becomes blocked or exceeds the risk threshold.

## Run

From the repository root:

```bash
python benchmarks/dynamic_replanning/dynamic_self_aware_replanning.py --seeds 30
```

Outputs:

```text
results/dynamic_self_aware_replanning.csv
results/dynamic_self_aware_replanning.md
```

## Metrics

- success rate,
- collision proxy,
- path length,
- number of replans,
- blocked events,
- risk spikes,
- nodes expanded,
- mean risk,
- max risk,
- recoverability,
- compute time.

## Scientific status

Readiness: **Prototype / Reproducible demo**

This is the first dynamic replanning layer. It is stronger than static-path planning because the robot must update its route online, but it is still a synthetic grid experiment.

## Limitations

- No physics engine.
- No continuous robot dynamics.
- No sensor latency.
- No ROS/Nav2 integration yet.
- Collision is a high-risk-cell proxy, not a physical contact event.

## Next milestones

- Add dynamic obstacle trajectories.
- Add prediction-aware future occupancy.
- Add confidence intervals and figures for this dynamic benchmark.
- Add ROS 2 / Nav2 adapter once the algorithmic benchmark is stable.
