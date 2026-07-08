# Uncertainty Model

DynNav represents each map cell with an obstacle probability `p(occupied)`. This compact belief is sufficient for deterministic risk-aware planning experiments and benchmark reproducibility.

## Model

- `p = 0` means the cell is treated as free.
- `p = 1` means the cell is treated as occupied.
- intermediate values represent uncertainty or partial observability.

A lightweight propagation function drifts probabilities toward 0.5 to approximate increasing uncertainty when observations become stale.

## Scientific motivation

Explicit probabilities allow the planner to distinguish unknown cells from confidently free cells. This supports risk-sensitive objectives such as tail-risk minimization.

## Engineering motivation

The representation is simple, serializable, and compatible with synthetic benchmarks. It can later be replaced by a richer mapper while preserving the planner interface.

## Limitations

The current implementation is not a full Bayesian occupancy-grid mapper. It does not yet model correlated cells, sensor fields of view, localization covariance, or temporal obstacle motion.
