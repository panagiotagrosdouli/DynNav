# SelfAwareAStar Benchmark

This benchmark compares classical A* with the first DynNav SelfAwareAStar prototype.

## Research question

Can a planner trade a slightly longer route for lower risk, higher recoverability, and useful information gain?

## Methods

- `classic_astar`: baseline unit-cost A* with Manhattan heuristic.
- `self_aware_astar`: A* variant whose transition cost includes risk, uncertainty, low recoverability, and information gain.

## Run

From the repository root:

```bash
python benchmarks/self_aware_astar/compare_astar.py
```

Outputs:

```text
results/self_aware_astar_comparison.csv
results/self_aware_astar_comparison.md
```

## Metrics

- success rate,
- collision proxy,
- path length,
- nodes expanded,
- mean risk,
- max risk,
- uncertainty integral,
- information gain,
- recoverability,
- compute time.

## Scientific status

Readiness: **Prototype / Reproducible demo**

This benchmark is synthetic. It is designed to test whether the objective behaves as expected before moving to randomized maps, dynamic obstacles, and ROS/Nav2 integration.

## Main limitation

The current benchmark uses one controlled map. The next milestone is a multi-seed randomized benchmark with statistical reporting and ablation runs.
