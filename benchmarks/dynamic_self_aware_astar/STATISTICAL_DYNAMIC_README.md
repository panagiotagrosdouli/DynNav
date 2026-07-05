# Dynamic SelfAwareAStar Statistical Evaluation

This document describes the statistical analysis workflow for the randomized dynamic benchmark.

## Purpose

The randomized dynamic benchmark compares static execution against online replanning. This statistical layer adds:

- bootstrap confidence intervals,
- standard deviations,
- Cohen's d effect sizes against `static_self_aware_astar`,
- a Markdown report for research review.

## Workflow

From the repository root:

```bash
python benchmarks/dynamic_self_aware_astar/randomized_dynamic_benchmark.py --seeds 50
python benchmarks/dynamic_self_aware_astar/statistical_analysis.py --bootstrap 1000
```

## Output

```text
results/dynamic_self_aware_astar_statistical_report.md
```

## Interpreting effect size

Cohen's d is computed as:

```text
d = (mean(method) - mean(static_self_aware_astar)) / pooled_std
```

For `success_rate` and `recoverability`, positive values usually indicate improvement.

For `collision_rate`, `path_length`, `replans`, `nodes_expanded`, `mean_risk`, `max_risk`, and `compute_time_ms`, negative values usually indicate improvement.

## Scientific status

This is synthetic benchmark evidence. It strengthens the static-vs-dynamic comparison but does not replace physics simulation, perception experiments, or real-robot evaluation.
