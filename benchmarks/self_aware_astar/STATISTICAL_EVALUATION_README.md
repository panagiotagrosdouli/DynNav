# SelfAwareAStar Statistical Evaluation

This document describes the statistical evaluation layer for the randomized SelfAwareAStar benchmark.

## Purpose

The randomized ablation benchmark reports averages across seeds. This statistical layer adds:

- bootstrap confidence intervals,
- standard deviations,
- Cohen's d effect sizes against classical A*,
- a Markdown report suitable for research review.

## Workflow

Run the randomized benchmark first:

```bash
python benchmarks/self_aware_astar/randomized_ablation_benchmark.py --seeds 50
```

Then run the statistical analysis:

```bash
python benchmarks/self_aware_astar/statistical_analysis.py \
  --input results/self_aware_astar_randomized_ablation.csv \
  --report results/self_aware_astar_statistical_report.md \
  --bootstrap 1000
```

## Output

```text
results/self_aware_astar_statistical_report.md
```

The report includes one table per metric:

- success rate,
- collision proxy,
- path length,
- nodes expanded,
- mean risk,
- max risk,
- information gain,
- recoverability,
- compute time.

## Effect-size interpretation

Cohen's d is computed as:

```text
d = (mean(method) - mean(classic_astar)) / pooled_std
```

The sign depends on the metric:

- For `success_rate`, `information_gain`, and `recoverability`, positive values usually indicate improvement.
- For `collision_rate`, `path_length`, `mean_risk`, `max_risk`, `nodes_expanded`, and `compute_time_ms`, negative values usually indicate improvement.

## Scientific status

This improves the credibility of the synthetic benchmark because the result is no longer just a mean table. It still does not prove real-robot performance.

## Limitations

- Confidence intervals are computed over synthetic randomized seeds.
- Collision is currently a high-risk-cell proxy, not a physics collision.
- The benchmark does not yet include dynamic obstacles, perception latency, or ROS/Nav2 execution.
