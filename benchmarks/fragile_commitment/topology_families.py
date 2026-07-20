"""Procedural topology families for the Fragile Commitment Benchmark.

The generators preserve a paired two-route structure while varying geometry, local
openness, risk noise, and dynamic closure location.  This keeps the benchmark
interpretable while moving beyond a single hand-crafted map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from scenario import FragileCommitmentScenario

Node = tuple[int, int]


@dataclass(frozen=True)
class TopologyConfig:
    family: str
    width: int = 31
    height: int = 19
    risk_mean: float = 0.08
    risk_std: float = 0.004
    fragile_risk_bias: float = 0.020
    resilient_risk_bias: float = 0.004


def _segment(a: Node, b: Node) -> list[Node]:
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


def _risk_field(
    rng: np.random.Generator,
    grid: np.ndarray,
    fragile_route: tuple[Node, ...],
    resilient_route: tuple[Node, ...],
    config: TopologyConfig,
) -> np.ndarray:
    risk = np.zeros_like(grid, dtype=float)
    free = grid == 0
    risk[free] = np.clip(
        config.risk_mean + rng.normal(0.0, config.risk_std, size=int(np.sum(free))),
        0.0,
        1.0,
    )
    for x, y in fragile_route:
        risk[y, x] += config.fragile_risk_bias
    for x, y in resilient_route:
        risk[y, x] += config.resilient_risk_bias
    return risk


def _two_route_scenario(
    seed: int,
    config: TopologyConfig,
    upper_y: int,
    lower_y: int,
    lower_half_width: int,
) -> FragileCommitmentScenario:
    rng = np.random.default_rng(seed)
    width, height = config.width, config.height
    if width < 21 or height < 13:
        raise ValueError("topology dimensions are too small")

    mid_y = height // 2
    start = (1, mid_y)
    goal = (width - 2, mid_y)
    left_x = 4
    right_x = width - 5

    fragile_route = _polyline(
        (start, (left_x, mid_y), (left_x, upper_y), (right_x, upper_y), (right_x, mid_y), goal)
    )
    resilient_route = _polyline(
        (start, (left_x, mid_y), (left_x, lower_y), (right_x, lower_y), (right_x, mid_y), goal)
    )

    grid = np.ones((height, width), dtype=np.uint8)
    for x, y in fragile_route:
        grid[y, x] = 0
    for x, y in resilient_route:
        grid[y, x] = 0

    y0 = max(1, lower_y - lower_half_width)
    y1 = min(height - 1, lower_y + lower_half_width + 1)
    grid[y0:y1, left_x - 1 : right_x + 2] = 0
    grid[mid_y - 1 : mid_y + 2, 0 : left_x + 2] = 0
    grid[mid_y - 1 : mid_y + 2, right_x - 1 : width] = 0

    closure_x = int(rng.integers(left_x + 3, right_x - 2))
    closure = (closure_x, upper_y)
    risk = _risk_field(rng, grid, fragile_route, resilient_route, config)
    return FragileCommitmentScenario(
        grid=grid,
        risk=risk,
        start=start,
        goal=goal,
        fragile_route=fragile_route,
        resilient_route=resilient_route,
        closure=closure,
    )


def generate_open(seed: int, config: TopologyConfig) -> FragileCommitmentScenario:
    """Wide detour and weak bottleneck contrast; useful as a near-neutral baseline."""
    return _two_route_scenario(seed, config, upper_y=5, lower_y=config.height - 6, lower_half_width=3)


def generate_bottleneck(seed: int, config: TopologyConfig) -> FragileCommitmentScenario:
    """Long one-cell fragile corridor against an open resilient region."""
    return _two_route_scenario(seed, config, upper_y=3, lower_y=config.height - 5, lower_half_width=2)


def generate_culdesac(seed: int, config: TopologyConfig) -> FragileCommitmentScenario:
    """Bottleneck family with side pockets that increase deceptive local openness."""
    scenario = _two_route_scenario(seed, config, upper_y=4, lower_y=config.height - 4, lower_half_width=2)
    grid = scenario.grid.copy()
    rng = np.random.default_rng(seed + 7919)
    for _ in range(3):
        x = int(rng.integers(7, config.width - 7))
        depth = int(rng.integers(2, 5))
        grid[4 : min(config.height, 5 + depth), x] = 0
    return FragileCommitmentScenario(
        grid=grid,
        risk=_risk_field(rng, grid, scenario.fragile_route, scenario.resilient_route, config),
        start=scenario.start,
        goal=scenario.goal,
        fragile_route=scenario.fragile_route,
        resilient_route=scenario.resilient_route,
        closure=scenario.closure,
    )


def generate_multiroute(seed: int, config: TopologyConfig) -> FragileCommitmentScenario:
    """Larger open lower class with extra cross-links and alternative local escapes."""
    scenario = _two_route_scenario(seed, config, upper_y=4, lower_y=config.height - 5, lower_half_width=3)
    grid = scenario.grid.copy()
    mid_y = config.height // 2
    for x in range(7, config.width - 7, 5):
        grid[mid_y : config.height - 2, x : x + 2] = 0
    rng = np.random.default_rng(seed + 104729)
    return FragileCommitmentScenario(
        grid=grid,
        risk=_risk_field(rng, grid, scenario.fragile_route, scenario.resilient_route, config),
        start=scenario.start,
        goal=scenario.goal,
        fragile_route=scenario.fragile_route,
        resilient_route=scenario.resilient_route,
        closure=scenario.closure,
    )


_GENERATORS: dict[str, Callable[[int, TopologyConfig], FragileCommitmentScenario]] = {
    "open": generate_open,
    "bottleneck": generate_bottleneck,
    "culdesac": generate_culdesac,
    "multiroute": generate_multiroute,
}


def available_families() -> tuple[str, ...]:
    return tuple(_GENERATORS)


def generate_topology(seed: int, config: TopologyConfig) -> FragileCommitmentScenario:
    try:
        generator = _GENERATORS[config.family]
    except KeyError as exc:
        raise ValueError(f"unknown topology family: {config.family}") from exc
    return generator(seed, config)
