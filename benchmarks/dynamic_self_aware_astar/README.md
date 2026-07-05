# Dynamic SelfAwareAStar

This benchmark introduces online replanning for SelfAwareAStar.

## Research question

Can the planner update its route when the remaining path becomes blocked or too risky after new map evidence arrives?

## What is implemented

The dynamic runner repeatedly:

1. plans from the current robot cell to the goal,
2. executes one step,
3. receives a map update,
4. checks whether the remaining path is blocked or above a risk threshold,
5. replans when necessary.

## Run

From the repository root:

```bash
python benchmarks/dynamic_self_aware_astar/run_dynamic_demo.py
```

Outputs:

```text
results/dynamic_self_aware_astar_demo.csv
results/dynamic_self_aware_astar_demo.md
```

## Metrics

- success rate,
- path length,
- replans,
- blocked replans,
- risk replans,
- nodes expanded,
- mean risk,
- max risk,
- information gain,
- recoverability,
- compute time.

## Scientific status

Readiness: **Prototype / Reproducible demo**

This is a controlled synthetic benchmark. It demonstrates online replanning logic, but it does not yet include physics simulation, sensing latency, dynamic obstacle prediction, or ROS/Nav2 integration.

## Next milestone

The next step is a randomized dynamic benchmark with moving obstacles and comparison against static planning without online replanning.
