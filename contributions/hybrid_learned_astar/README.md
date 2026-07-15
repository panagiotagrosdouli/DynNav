# Hybrid Learned A* with Uncertainty-Guided Fallback

[Back to the repository README](../../README.md)

## Purpose

This contribution studies a hybrid search rule that uses a learned cost-to-go estimate when predictive uncertainty is below a threshold and falls back to a classical geometric heuristic otherwise.

## Maturity

**Research Prototype / Synthetic Validation.** The repository contains Python experiment code and tests for the planner family. The module is not a formal safety mechanism and has not been validated on ROS2, Nav2, Gazebo, or hardware through this README.

## Decision rule

For a node `n`, the planner receives a predicted mean heuristic `h_mean(n)` and uncertainty `h_std(n)`:

- use `h_mean(n)` when `h_std(n) <= tau`;
- otherwise use the configured admissible fallback heuristic.

The threshold `tau` controls how often the learned estimate is trusted. Admissibility and optimality depend on the fallback behavior and the exact implementation; they must be established by the corresponding tests rather than inferred from this description.

## Implementation and tests

- **Contribution directory:** [`contributions/hybrid_learned_astar/`](./)
- **Experiment entry point:** [`experiments/run_hybrid_experiment.py`](experiments/run_hybrid_experiment.py)
- **Repository tests:** [`../../tests/`](../../tests/)

## Run

From the repository root:

```bash
PYTHONPATH=. python -m contributions.hybrid_learned_astar.experiments.run_hybrid_experiment --eval-grids 100 --seed 42 --taus 0.5 1.0 1.5 2.0 3.0
```

The command performs synthetic grid evaluation. Generated metrics or figures should only be treated as evidence when the exact configuration, seed, raw output, and generation command are committed and linked.

## Expected evaluation fields

- path-found rate;
- expanded nodes;
- path length or cost;
- fallback rate;
- predictive uncertainty;
- execution time.

## Limitations

- Learned-heuristic quality depends on the training data and model calibration.
- A lower expansion count does not by itself establish safety or generalization.
- Synthetic grid results do not establish real-time robot performance.
- No hardware or ROS2 validation is claimed here.
