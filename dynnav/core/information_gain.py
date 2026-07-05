"""Information-gain utilities for active navigation."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from dynnav.core.navigation_state import GridCell


def binary_entropy(probability: float) -> float:
    """Return Bernoulli entropy in bits.

    Occupancy probabilities near 0.5 have high entropy; probabilities near 0 or
    1 have low entropy. This is a simple proxy for map uncertainty.
    """
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"probability must be in [0, 1], got {probability!r}")
    if probability in (0.0, 1.0):
        return 0.0
    return -probability * math.log2(probability) - (1.0 - probability) * math.log2(1.0 - probability)


def expected_information_gain(
    path: Sequence[GridCell],
    occupancy_belief: Mapping[GridCell, float],
    sensor_radius: int = 1,
) -> float:
    """Estimate normalized map information gain along a path.

    The score sums the entropy of cells visible from the candidate path and
    normalizes by the maximum possible entropy of the visible set.

    Args:
        path: Candidate path cells.
        occupancy_belief: Mapping from cell to occupancy probability.
        sensor_radius: Manhattan radius around each path cell considered visible.

    Returns:
        A normalized information-gain proxy in [0, 1].
    """
    if sensor_radius < 0:
        raise ValueError("sensor_radius must be non-negative")
    if not path or not occupancy_belief:
        return 0.0

    visible: set[GridCell] = set()
    for x, y in path:
        for dx in range(-sensor_radius, sensor_radius + 1):
            for dy in range(-sensor_radius, sensor_radius + 1):
                if abs(dx) + abs(dy) <= sensor_radius:
                    cell = (x + dx, y + dy)
                    if cell in occupancy_belief:
                        visible.add(cell)

    if not visible:
        return 0.0

    entropy_sum = sum(binary_entropy(occupancy_belief[cell]) for cell in visible)
    return entropy_sum / len(visible)
