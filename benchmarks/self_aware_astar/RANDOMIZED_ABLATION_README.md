# SelfAwareAStar Randomized Ablation Benchmark

This benchmark extends the controlled SelfAwareAStar corridor demo into a multi-seed randomized evaluation.

## Research question

Does the full SelfAwareAStar objective reduce risk and improve recoverability across many synthetic maps, and which terms are responsible for the effect?

## Compared methods

| Method | Description |
|---|---|
| `classic_astar` | Unit-cost A* baseline. |
| `self_aware_full` | Risk + uncertainty + recoverability + information gain. |
| `ablation_no_risk` | Removes risk and recoverability penalties. |
| `ablation_no_uncertainty` | Removes uncertainty penalty. |
| `ablation_no_information_gain` | Removes information-gain reward. |

## Run

From the repository root:

```bash
python benchmarks/self_aware_astar/randomized_ablation_benchmark.py --seeds 50
```

Outputs:

```text
results/self_aware_astar_randomized_ablation.csv
results/self_aware_astar_randomized_ablation.md
```

## Metrics

The benchmark reports:

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

## Scientific interpretation

This is stronger than a single-map demo because it evaluates repeated randomized scenarios and includes ablations. However, it is still a synthetic benchmark. It should be interpreted as controlled algorithmic evidence, not as real-world robot validation.

## Next milestone

To reach benchmark-ready status, the next step is to add:

- confidence intervals or bootstrap intervals,
- map families with different obstacle densities,
- dynamic obstacle variants,
- generated figures,
- CI smoke run with a small number of seeds.
