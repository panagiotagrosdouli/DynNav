# Predictive Dynamic Risk Maps

This benchmark introduces a predictive risk layer for DynNav.

## Research question

Can a planner avoid cells that are currently safe but predicted to become risky when the robot reaches them?

## What is implemented

- `PredictiveRiskMap`: stores `risk(cell, time_step)`.
- `StaticRiskPredictor`: repeats the current risk map over time.
- `ConstantVelocityRiskPredictor`: predicts future risk from moving risk sources.
- `PredictiveSelfAwareAStar`: uses time-indexed predicted risk inside A* transition costs.

## Run

From the repository root:

```bash
python benchmarks/predictive_navigation/run_predictive_demo.py
```

Outputs:

```text
results/predictive_navigation_demo.csv
results/predictive_navigation_demo.md
```

## Compared methods

| Method | Description |
|---|---|
| `self_aware_astar` | Plans with current risk only. |
| `predictive_self_aware_astar` | Plans with predicted risk at the estimated time of arrival. |

## Metrics

- success rate,
- predicted collision proxy,
- path length,
- predicted mean risk,
- predicted max risk,
- avoided future hazard,
- recoverability,
- nodes expanded,
- compute time.

## Scientific status

Readiness: **Prototype / Reproducible demo**

This is a controlled synthetic demonstration. The next step is a randomized benchmark with moving hazards and prediction-error analysis.

## Main limitation

The current predictor assumes constant velocity and perfect knowledge of the moving risk source. Future work should add noisy prediction, incorrect forecasts, replanning after prediction failure, and simulator traces.
