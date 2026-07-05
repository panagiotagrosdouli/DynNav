# Randomized Dynamic SelfAwareAStar Benchmark

This benchmark compares static execution against online dynamic replanning.

## Research question

Does online replanning improve navigation robustness when new map evidence changes the traversability or risk of the remaining route?

## Compared methods

| Method | Description |
|---|---|
| `static_self_aware_astar` | Plans once with SelfAwareAStar and executes the original path without replanning. |
| `dynamic_self_aware_astar` | Replans when the remaining path becomes blocked or exceeds a risk threshold. |

## Run

From the repository root:

```bash
python benchmarks/dynamic_self_aware_astar/randomized_dynamic_benchmark.py --seeds 50
```

Outputs:

```text
results/dynamic_self_aware_astar_randomized.csv
results/dynamic_self_aware_astar_randomized.md
```

## Metrics

The benchmark reports:

- success rate,
- collision proxy,
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

Readiness: **Prototype / Benchmark candidate**

This benchmark is stronger than a single dynamic demo because it evaluates repeated randomized scenarios and includes a static-vs-dynamic comparison. It is still synthetic and should not be presented as real-robot evidence.

## Next milestone

- Add confidence intervals and effect sizes.
- Add dynamic obstacle prediction.
- Add physics simulation or ROS/Nav2 traces.
- Add failure-case taxonomy for blocked path, high-risk path, and timeout failures.
