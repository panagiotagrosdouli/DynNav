"""Recoverability metrics for Contribution 04.

Contribution 04 studies whether a robot should commit to a state when it may not
be able to safely return or recover later. This module turns that idea into small,
auditable metrics that can be used by experiments and planners.

The metrics are intentionally lightweight:

- returnability: can the robot reach a trusted base from a candidate state?
- escape option count: how many safe local actions remain available?
- bottleneck score: how constrained is the local neighbourhood?
- recoverability score: a normalized summary of future recovery freedom.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
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

    The score combines three intuitions:

    1. Returnability: a path to base exists.
    2. Local freedom: more escape options are better.
    3. Local clutter: high obstacle density reduces recovery margin.

    The output is not a formal safety guarantee. It is a transparent planning
    signal that can be audited and later replaced by stronger reachability tools.
    """
    dist = shortest_path_distance(grid, node, base)
    returnable = bool(np.isfinite(dist))
    escape_options = len(neighbours4(grid, node)) if is_free(grid, node) else 0
    density = local_obstacle_density(grid, node, radius=obstacle_radius)
    bottleneck = bottleneck_score(grid, node)

    if max_return_distance is None:
        max_return_distance = float(grid.shape[0] + grid.shape[1])
    distance_factor = 0.0 if not returnable else max(0.0, 1.0 - dist / max(max_return_distance, 1.0))
    escape_factor = escape_options / 4.0
    clutter_factor = max(0.0, 1.0 - density)

    score = 0.50 * distance_factor + 0.30 * escape_factor + 0.20 * clutter_factor
    if not returnable:
        score = 0.0
    score = float(np.clip(score, 0.0, 1.0))
    irreversibility = float(1.0 - score)

    return RecoverabilityReport(
        node=node,
        base=base,
        returnable=returnable,
        distance_to_base=float(dist),
        escape_options=int(escape_options),
        bottleneck_score=bottleneck,
        local_obstacle_density=density,
        recoverability_score=score,
        irreversibility_score=irreversibility,
    )


def evaluate_path_recoverability(grid: Grid, path: Iterable[Node], base: Node) -> dict[str, float | int | bool]:
    reports = [recoverability_score(grid, node, base) for node in path]
    if not reports:
        raise ValueError("path must contain at least one node")
    scores = np.asarray([r.recoverability_score for r in reports], dtype=float)
    irreversibility = np.asarray([r.irreversibility_score for r in reports], dtype=float)
    return {
        "path_len": len(reports),
        "all_returnable": all(r.returnable for r in reports),
        "min_recoverability": float(np.min(scores)),
        "mean_recoverability": float(np.mean(scores)),
        "max_irreversibility": float(np.max(irreversibility)),
        "mean_irreversibility": float(np.mean(irreversibility)),
        "worst_escape_options": int(min(r.escape_options for r in reports)),
    }
