# SelfAwareAStar Plotting Workflow

This document explains how to generate figures for the randomized SelfAwareAStar benchmark.

## Purpose

The benchmark and statistical scripts produce CSV and Markdown reports. The plotting script adds visual summaries for research communication.

Generated figures include:

- mean risk,
- max risk,
- recoverability,
- information gain,
- path length,
- compute time.

Each plot shows method-level means with standard-deviation error bars across randomized synthetic maps.

## Full workflow

From the repository root:

```bash
python benchmarks/self_aware_astar/randomized_ablation_benchmark.py --seeds 50
python benchmarks/self_aware_astar/statistical_analysis.py --bootstrap 1000
python benchmarks/self_aware_astar/plot_randomized_results.py
```

## Outputs

```text
results/self_aware_astar_randomized_ablation.csv
results/self_aware_astar_randomized_ablation.md
results/self_aware_astar_statistical_report.md
results/self_aware_astar_figure_index.md
results/figures/self_aware_astar/*.png
```

## Dependency

The plotting script requires `matplotlib`:

```bash
pip install matplotlib
```

The core planner and benchmark code do not require matplotlib.

## Scientific interpretation

The figures are communication aids, not a substitute for the statistical report. Use them together with confidence intervals, effect sizes, and limitations.

## Limitation

The plots summarize synthetic benchmark data. They do not represent real-robot validation or physics-based simulation performance.
