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


Εξαιρετικά. Τα δεδομένα πλέον είναι αρκετά για να γράψουμε το επίσημο αποτέλεσμα του C01.

# Results (για README)

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




## Current Validation Results

A 400-task validation run was executed with four obstacle-density regimes: easy (10%), medium (20%), hard (30%), and very hard (40%). In the local validation environment, the learned checkpoint was not available, so `learned_raw` and `learned_manhattan_clipped` fell back to Manhattan. Therefore the current results validate the benchmark protocol and the classical baseline, but should **not** be used as final evidence for learned-heuristic improvement.

| Scenario | Dijkstra expansions | A* Manhattan expansions | Reduction vs Dijkstra |
|---|---:|---:|---:|
| Easy, 10% obstacles | 901.00 ± 300.04 | 202.30 ± 123.15 | 77.55% |
| Medium, 20% obstacles | 862.29 ± 278.97 | 199.46 ± 127.63 | 76.87% |
| Hard, 30% obstacles | 668.63 ± 259.39 | 204.58 ± 142.70 | 69.40% |
| Very hard, 40% obstacles | 466.81 ± 171.70 | 240.99 ± 155.14 | 48.37% |

All sampled tasks were reachable and all evaluated methods returned valid paths in this validation run. The path cost of the Manhattan baseline matched Dijkstra in all successful trials, as expected for admissible A*.

## Interpreting Learned Results

The final learned-heuristic claim should be made only after running `statistical_validation.py` with a trained checkpoint available. A publishable claim should have the following form:

```text
Across N benchmark tasks, learned A* reduced node expansions by X% ± Y%
relative to A* Manhattan while preserving optimal path cost on Z% of tasks.
```

Until that checkpoint-backed run is available, the honest claim is:

> C01 now provides a reproducible statistical evaluation protocol and a corrected admissibility-aware A* implementation. The current baseline run confirms the expected efficiency advantage of Manhattan A* over Dijkstra, but does not yet establish learned-heuristic improvement over Manhattan.

## Limitations

- The raw neural heuristic is not guaranteed admissible.
- The clipped learned heuristic is admissible but may be no more informative than Manhattan.
- Final learned-performance claims require the trained checkpoint and a stored validation CSV.
- Runtime measurements are machine-dependent and should be reported with hardware/software context.

## Integration

- **Foundation** for all other planning contributions.
- **Extended by**: Contribution 12 (diffusion risk maps as cost).
- **Extended by**: Contribution 18 (CBF safety as hard constraint).
