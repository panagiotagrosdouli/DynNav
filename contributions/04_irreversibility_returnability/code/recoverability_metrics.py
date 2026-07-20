"""Recoverability metrics for Contribution 04.

Contribution 04 studies whether a robot should commit to a state when it may not
be able to safely return or recover later. This module turns that idea into small,
auditable metrics that can be used by experiments and planners.

The metrics distinguish two questions:

- returnability: does a path back to a trusted base exist?
- recoverability: how much future recovery freedom remains along a route?

The implementation is intentionally transparent. It is a planning signal and an
experimental instrument, not a formal safety certificate.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

Grid = np.ndarray
Node = tuple[int, int]


@dataclass(frozen=True)
class RecoverabilityReport:
    node: Node
    base: Node
    returnable: bool
    distance_to_base: float
    escape_options: int
    bottleneck_score: float
    local_obstacle_density: float
    recoverability_score: float
    irreversibility_score: float

    def to_dict(self) -> dict[str, float | int | bool | str]:
        row = asdict(self)
        row["node"] = str(self.node)
        row["base"] = str(self.base)
        return row


@dataclass(frozen=True)
class PathRecoverabilityProfile:
    """Route-level summary of retained recovery freedom.

    ``cumulative_recoverability_loss`` measures every downward transition in the
    score, rather than only the endpoint difference. A route that repeatedly
    enters fragile regions therefore receives a larger penalty.

    ``bottleneck_exposure`` is the mean local bottleneck score along the route.
    Keeping it separate from the node score makes route-level ablations possible.
    """

    path_len: int
    all_returnable: bool
    min_recoverability: float
    mean_recoverability: float
    terminal_recoverability: float
    cumulative_recoverability_loss: float
    maximum_single_step_loss: float
    bottleneck_exposure: float
    max_irreversibility: float
    mean_irreversibility: float
    worst_escape_options: int

    def penalty(
        self,
        minimum_weight: float = 1.0,
        degradation_weight: float = 1.0,
        bottleneck_weight: float = 1.0,
    ) -> float:
        """Return an interpretable route-level fragility penalty.

        The three non-negative terms correspond to:

        1. the weakest recoverability point on the route;
        2. accumulated loss of recoverability during commitment;
        3. exposure to locally constrained states.
        """
        weights = (minimum_weight, degradation_weight, bottleneck_weight)
        if any(weight < 0.0 for weight in weights):
            raise ValueError("penalty weights must be non-negative")
        return float(
            minimum_weight * (1.0 - self.min_recoverability)
            + degradation_weight * self.cumulative_recoverability_loss
            + bottleneck_weight * self.bottleneck_exposure
        )

    def to_dict(self) -> dict[str, float | int | bool]:
        return asdict(self)


def in_bounds(grid: Grid, node: Node) -> bool:
    x, y = node
    height, width = grid.shape
    return 0 <= x < width and 0 <= y < height


def is_free(grid: Grid, node: Node) -> bool:
    x, y = node
    return in_bounds(grid, node) and grid[y, x] == 0


def neighbours4(grid: Grid, node: Node) -> list[Node]:
    x, y = node
    out: list[Node] = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nxt = (x + dx, y + dy)
        if is_free(grid, nxt):
            out.append(nxt)
    return out


def shortest_path_distance(grid: Grid, start: Node, goal: Node) -> float:
    if not is_free(grid, start) or not is_free(grid, goal):
        return float("inf")
    q: deque[Node] = deque([start])
    dist: dict[Node, int] = {start: 0}
    while q:
        curr = q.popleft()
        if curr == goal:
            return float(dist[curr])
        for nxt in neighbours4(grid, curr):
            if nxt not in dist:
                dist[nxt] = dist[curr] + 1
                q.append(nxt)
    return float("inf")


def local_obstacle_density(grid: Grid, node: Node, radius: int = 2) -> float:
    if radius < 0:
        raise ValueError("radius must be non-negative")
    x, y = node
    height, width = grid.shape
    x0 = max(0, x - radius)
    x1 = min(width, x + radius + 1)
    y0 = max(0, y - radius)
    y1 = min(height, y + radius + 1)
    window = grid[y0:y1, x0:x1]
    if window.size == 0:
        return 1.0
    return float(np.mean(window != 0))


def bottleneck_score(grid: Grid, node: Node) -> float:
    """Return 1 for no escape options and 0 for four local options."""
    options = len(neighbours4(grid, node)) if is_free(grid, node) else 0
    return float(1.0 - options / 4.0)


def recoverability_score(
    grid: Grid,
    node: Node,
    base: Node,
    max_return_distance: float | None = None,
    obstacle_radius: int = 2,
) -> RecoverabilityReport:
    """Compute a normalized recoverability estimate for one candidate state.

    The score combines three auditable quantities: return distance, local escape
    options, and local obstacle density. It is deliberately not presented as a
    formal guarantee.
    """
    dist = shortest_path_distance(grid, node, base)
    returnable = bool(np.isfinite(dist))
    escape_options = len(neighbours4(grid, node)) if is_free(grid, node) else 0
    density = local_obstacle_density(grid, node, radius=obstacle_radius)
    bottleneck = bottleneck_score(grid, node)

    if max_return_distance is None:
        max_return_distance = float(grid.shape[0] + grid.shape[1])
    if max_return_distance <= 0.0:
        raise ValueError("max_return_distance must be positive")

    distance_factor = 0.0 if not returnable else max(0.0, 1.0 - dist / max_return_distance)
    escape_factor = escape_options / 4.0
    clutter_factor = max(0.0, 1.0 - density)

    score = 0.50 * distance_factor + 0.30 * escape_factor + 0.20 * clutter_factor
    if not returnable:
        score = 0.0
    score = float(np.clip(score, 0.0, 1.0))

    return RecoverabilityReport(
        node=node,
        base=base,
        returnable=returnable,
        distance_to_base=float(dist),
        escape_options=int(escape_options),
        bottleneck_score=bottleneck,
        local_obstacle_density=density,
        recoverability_score=score,
        irreversibility_score=float(1.0 - score),
    )


def build_path_recoverability_profile(
    grid: Grid,
    path: Iterable[Node],
    base: Node,
    max_return_distance: float | None = None,
    obstacle_radius: int = 2,
) -> PathRecoverabilityProfile:
    """Evaluate route-level recoverability and its degradation profile."""
    reports = [
        recoverability_score(
            grid,
            node,
            base,
            max_return_distance=max_return_distance,
            obstacle_radius=obstacle_radius,
        )
        for node in path
    ]
    if not reports:
        raise ValueError("path must contain at least one node")

    scores = np.asarray([report.recoverability_score for report in reports], dtype=float)
    irreversibility = 1.0 - scores
    bottlenecks = np.asarray([report.bottleneck_score for report in reports], dtype=float)
    losses = np.maximum(0.0, scores[:-1] - scores[1:])

    return PathRecoverabilityProfile(
        path_len=len(reports),
        all_returnable=all(report.returnable for report in reports),
        min_recoverability=float(np.min(scores)),
        mean_recoverability=float(np.mean(scores)),
        terminal_recoverability=float(scores[-1]),
        cumulative_recoverability_loss=float(np.sum(losses)),
        maximum_single_step_loss=float(np.max(losses)) if losses.size else 0.0,
        bottleneck_exposure=float(np.mean(bottlenecks)),
        max_irreversibility=float(np.max(irreversibility)),
        mean_irreversibility=float(np.mean(irreversibility)),
        worst_escape_options=int(min(report.escape_options for report in reports)),
    )


def evaluate_path_recoverability(
    grid: Grid,
    path: Iterable[Node],
    base: Node,
) -> dict[str, float | int | bool]:
    """Backward-compatible dictionary interface for experiment scripts."""
    return build_path_recoverability_profile(grid, path, base).to_dict()
