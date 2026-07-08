"""Risk and uncertainty utilities for belief-space navigation."""

from __future__ import annotations

import numpy as np


def cvar(samples: np.ndarray, alpha: float = 0.9) -> float:
    """Compute Conditional Value-at-Risk for finite cost samples.

    CVaR is the mean of the upper tail above the alpha quantile. In this
    repository it is used as a conservative summary of collision or traversal
    costs under map uncertainty.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    values = np.asarray(samples, dtype=float).ravel()
    if values.size == 0:
        return 0.0
    threshold = np.quantile(values, alpha)
    tail = values[values >= threshold]
    return float(tail.mean()) if tail.size else float(threshold)


def entropy(probability: np.ndarray) -> np.ndarray:
    """Return Bernoulli entropy for occupancy probabilities."""
    p = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    return -(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))


def mission_risk(path_probabilities: list[float], alpha: float = 0.9) -> float:
    """Estimate path risk from occupancy probabilities along a trajectory."""
    if not path_probabilities:
        return 1.0
    samples = np.asarray(path_probabilities, dtype=float)
    collision_probability = 1.0 - float(np.prod(1.0 - np.clip(samples, 0.0, 1.0)))
    return max(collision_probability, cvar(samples, alpha=alpha))


def propagate_uncertainty(
    occupancy: np.ndarray,
    process_noise: float = 0.02,
) -> np.ndarray:
    """Apply a lightweight uncertainty propagation step.

    This is a deterministic prototype, not a replacement for a full Bayesian
    mapper. It drifts probabilities toward maximum uncertainty to emulate stale
    or unobserved map cells between perception updates.
    """
    grid = np.asarray(occupancy, dtype=float)
    return np.clip(grid + process_noise * (0.5 - grid), 0.0, 1.0)
