# Hybrid Learned A* with Uncertainty-Aware Fallback

[Back to the repository README](../../README.md)

## Purpose

This module evaluates a hybrid A* rule that uses a learned cost-to-go estimate when predictive uncertainty is below a threshold and falls back to a classical geometric heuristic otherwise.

## Maturity

**Research Prototype / Synthetic Validation.** The repository contains Python experiment code and tests for this planner family. This module is not a formal safety mechanism and has not been validated on ROS2, Gazebo, or hardware through this document.

## Decision rule

For a node `n`, the planner receives a predicted mean heuristic `h_mean(n)` and uncertainty `h_std(n)`:

- use `h_mean(n)` when `h_std(n) <= tau`;
- otherwise use the configured fallback heuristic.

The threshold `tau` controls how often the learned estimate is trusted. Optimality and admissibility depend on the exact fallback and implementation and must be established by tests.

## Run

From the repository root:

```bash
PYTHONPATH=. python -m contributions.hybrid_learned_astar.experiments.run_hybrid_experiment \
  --eval-grids 100 \
  --seed 42 \
  --taus 0.5 1.0 1.5 2.0 3.0
```

## Evaluation fields

- path-found rate;
- expanded nodes;
- path length or cost;
- fallback rate;
- predictive uncertainty;
- execution time.

## Limitations

- Learned-heuristic quality depends on training data and uncertainty calibration.
- Lower node expansion does not establish safety or generalization.
- Synthetic grid results do not establish real-time robot performance.
