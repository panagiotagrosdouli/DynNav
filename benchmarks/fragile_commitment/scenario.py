"""Controlled two-route scenario for the Fragile Commitment Benchmark."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

Node = tuple[int, int]


@dataclass(frozen=True)
class FragileCommitmentScenario:
    grid: np.ndarray
    risk: np.ndarray
    start: Node
    goal: Node
    fragile_route: tuple[Node, ...]
    resilient_route: tuple[Node, ...]
    closure: Node


def _segment(a: Node, b: Node) -> list[Node]:
    """Return an axis-aligned inclusive grid segment."""
    ax, ay = a
    bx, by = b
    if ax != bx and ay != by:
        raise ValueError("segments must be axis aligned")
    dx = 0 if ax == bx else (1 if bx > ax else -1)
    dy = 0 if ay == by else (1 if by > ay else -1)
    length = abs(bx - ax) + abs(by - ay)
    return [(ax + i * dx, ay + i * dy) for i in range(length + 1)]


def _polyline(points: tuple[Node, ...]) -> tuple[Node, ...]:
    path: list[Node] = []
    for index, (a, b) in enumerate(zip(points, points[1:])):
        segment = _segment(a, b)
        path.extend(segment if index == 0 else segment[1:])
    return tuple(path)


def generate_scenario(seed: int = 0) -> FragileCommitmentScenario:
    """Generate a reproducible counterexample with two explicit route classes.

    Seed-dependent noise perturbs risk values without changing the topology. The
    narrow upper route remains shorter and slightly lower risk, while the lower
    route retains substantially more local recovery freedom.
    """
    rng = np.random.default_rng(seed)
    width, height = 25, 15
    grid = np.ones((height, width), dtype=np.uint8)

    start = (1, 7)
    goal = (23, 7)
    fragile_route = _polyline((start, (4, 7), (4, 4), (20, 4), (20, 7), goal))
    resilient_route = _polyline((start, (4, 7), (4, 11), (20, 11), (20, 7), goal))

    # Carve a one-cell upper corridor and a five-cell-tall lower open region.
    for x, y in fragile_route:
        grid[y, x] = 0
    grid[9:14, 3:22] = 0
    for x, y in resilient_route:
        grid[y, x] = 0
    grid[6:9, 0:6] = 0
    grid[6:9, 19:25] = 0

    risk = np.zeros_like(grid, dtype=float)
    free = grid == 0
    risk[free] = np.clip(0.08 + rng.normal(0.0, 0.004, size=int(np.sum(free))), 0.0, 1.0)

    # Keep risks close while making the fragile route attractive to risk-only search.
    for x, y in fragile_route:
        risk[y, x] += 0.004
    for x, y in resilient_route:
        risk[y, x] += 0.010

    closure = (12, 4)
    return FragileCommitmentScenario(
        grid=grid,
        risk=risk,
        start=start,
        goal=goal,
        fragile_route=fragile_route,
        resilient_route=resilient_route,
        closure=closure,
    )


def apply_closure(scenario: FragileCommitmentScenario) -> np.ndarray:
    """Return a copy of the occupancy grid after the dynamic event."""
    changed = scenario.grid.copy()
    x, y = scenario.closure
    changed[y, x] = 1
    return changed
