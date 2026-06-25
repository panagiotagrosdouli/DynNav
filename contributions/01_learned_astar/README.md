# Contribution 01 — Learned A* Heuristics

[![Module](https://img.shields.io/badge/Module-01-purple)](.) [![Type](https://img.shields.io/badge/Type-Learning--Augmented%20Planning-blue)](.) [![Status](https://img.shields.io/badge/Status-Core-brightgreen)](.)

## Overview

This contribution studies whether a learned heuristic can improve A* search efficiency on grid-world navigation tasks while preserving the path-cost guarantees expected from classical graph search.

The implementation now separates two cases explicitly:

1. **Raw learned heuristic**: may reduce expansions, but does not automatically guarantee optimality.
2. **Manhattan-clipped learned heuristic**: uses `min(h_theta, h_manhattan)` and is admissible for 4-neighbour, unit-cost grids, but is conservative.

This distinction is important: learned heuristics should not be described as optimality-preserving unless the admissibility condition is enforced or empirically verified against an optimal baseline.

## Research Question

> **RQ1:** Can a learned heuristic reduce planning effort while preserving optimal path cost under a clearly stated admissibility policy?

## Method

```text
Training: past (state, true_cost_to_goal) pairs → MLP regression → h_theta(s)
Inference, raw mode: A* uses max(0, h_theta(s))
Inference, clipped mode: A* uses min(max(0, h_theta(s)), h_manhattan(s))
Guarantee: clipped mode is admissible when Manhattan is admissible
```

For this 4-neighbour, unit-cost grid, Manhattan distance is the correct classical admissible baseline:

```text
h(n) = |x_goal - x_n| + |y_goal - y_n|
```

## Files

```text
01_learned_astar/
├── README.md
├── experiments/
│   ├── astar_learned_heuristic.py      # Corrected C01 A* core
│   ├── eval_astar_learned.py           # Multi-trial evaluation script
│   └── statistical_validation.py       # Density sweep + summary statistics
└── results/
    ├── c01_validation_trials.csv       # Per-task/per-method rows, generated
    └── c01_validation_summary.csv      # Aggregated statistics, generated
```

## Quick Start

Run the basic multi-trial evaluation:

```bash
python contributions/01_learned_astar/experiments/eval_astar_learned.py \
  --trials 100 \
  --out contributions/01_learned_astar/results/astar_eval_results.csv
```

Run the full statistical validation benchmark:

```bash
python contributions/01_learned_astar/experiments/statistical_validation.py \
  --grid-size 40 \
  --trials-per-density 100 \
  --min-distance 20
```

The validation benchmark compares:

| Method | Description | Optimality status |
|---|---|---|
| `dijkstra_h0` | A* with zero heuristic | Optimal |
| `astar_manhattan` | A* with Manhattan heuristic | Optimal |
| `learned_raw` | Neural heuristic without clipping | Must be checked empirically |
| `learned_manhattan_clipped` | Neural heuristic clipped by Manhattan | Admissible on this grid model |




## Experimental Setup

* 100 random start-goal trials
* 40×40 grid environment
* Classical A* baseline
* Learned A* using the trained neural heuristic
* CPU execution
* Same planning tasks for both planners

## Quantitative Results

| Metric          |      Classic A* |      Learned A* |
| --------------- | --------------: | --------------: |
| Success Rate    |            100% |            100% |
| Path Length     |   42.21 ± 11.40 |   42.21 ± 11.40 |
| Node Expansions | 461.23 ± 267.58 | 266.78 ± 212.18 |
| Runtime (ms)    |     1.17 ± 0.68 |   18.31 ± 11.34 |

### Expansion Reduction

[
Reduction=\left(1-0.5720\right)\times100
]

Reduction=(1-0.5720)\times100

Result:

```text
42.8% fewer node expansions
```

### Path Optimality

```text
Delta path length = 0.0000 ± 0.0000
```

The learned heuristic produced paths of identical length to the classical A* baseline across all evaluated trials.

---

# CLAIMS_EVIDENCE.md (C01)

## Claim

**Contribution 01 introduces a learned heuristic for A* search that substantially reduces search effort while preserving solution quality.**

### Evidence

Dataset:

```text
100 randomized start-goal trials
```

Observed metrics:

```text
Success rate: 100%
Path length difference: 0
Expansion reduction: 42.8%
```

Measured values:

```text
Classic expansions:
461.23 ± 267.58

Learned expansions:
266.78 ± 212.18
```

```text
Expansion ratio:
0.5720 ± 0.2335
```

Interpretation:

```text
The learned heuristic reduced node expansions by approximately
42.8% while maintaining identical path lengths on all successful
trials.
```

### Limitation

```text
Runtime increased because neural-network inference introduces
additional computation per node expansion.
```

Observed:

```text
Classic runtime:
1.17 ms

Learned runtime:
18.31 ms
```

Therefore:

```text
Contribution 01 should be described as a search-efficiency
improvement rather than a runtime-speed improvement.
```

## Validated Results

A full validation benchmark consisting of 400 navigation tasks was executed across four obstacle-density regimes:

* Easy (10%)
* Medium (20%)
* Hard (30%)
* Very Hard (40%)

All methods achieved a 100% success rate and produced paths with identical mean path cost within each scenario.

### Node Expansion Performance

| Scenario  | Manhattan A* | Learned Raw | Learned Clipped |
| --------- | -----------: | ----------: | --------------: |
| Easy      |       202.30 |      149.63 |          210.75 |
| Medium    |       199.46 |      171.41 |          211.63 |
| Hard      |       204.58 |      200.53 |          210.64 |
| Very Hard |       240.99 |      244.04 |          247.02 |

### Key Findings

* Learned Raw reduced node expansions by approximately 26.0% on easy environments.
* Learned Raw reduced node expansions by approximately 14.1% on medium environments.
* Improvements became negligible on hard environments.
* No measurable advantage was observed on very hard environments.
* Learned Manhattan Clipped preserved admissibility but did not outperform Manhattan A*.
* Runtime increased due to neural-network inference overhead.

### Conclusion

The learned heuristic improves search efficiency primarily in easier navigation settings. As obstacle density increases, the learned model becomes less informative relative to the Manhattan heuristic. These results suggest that future work should focus on richer learned representations and uncertainty-aware planning strategies.


## Integration

- **Foundation** for all other planning contributions.
- **Extended by**: Contribution 12 (diffusion risk maps as cost).
- **Extended by**: Contribution 18 (CBF safety as hard constraint).
