"""C07 — Next-Best-View: frontier-based exploration."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS
from ._common import (
    apply_theme,
    explanation_block,
    grid_heatmap_trace,
    interpretation_block,
    make_grid_with_obstacles,
    metrics_row,
    point_trace,
    section_header,
    square_axes,
)


def _build_known_mask(grid: np.ndarray, robot: tuple[int, int], radius: int) -> np.ndarray:
    H, W = grid.shape
    Y, X = np.mgrid[0:H, 0:W]
    d = np.maximum(np.abs(X - robot[0]), np.abs(Y - robot[1]))
    return (d <= radius).astype(np.float32)


def _frontier_cells(known: np.ndarray, grid: np.ndarray) -> list[tuple[int, int]]:
    """Frontier = known-free cell adjacent to an unknown cell."""
    frontiers = []
    H, W = known.shape
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if known[y, x] < 0.5 or grid[y, x] > 0.5:
                continue
            # check 4-neighborhood for unknown
            if (known[y - 1, x] < 0.5 or known[y + 1, x] < 0.5
                    or known[y, x - 1] < 0.5 or known[y, x + 1] < 0.5):
                frontiers.append((x, y))
    return frontiers


def _score_frontier(
    frontier: tuple[int, int],
    robot: tuple[int, int],
    grid: np.ndarray,
    known: np.ndarray,
    horizon: int,
) -> float:
    """Information gain proxy: count of unknown cells within horizon of frontier."""
    fx, fy = frontier
    H, W = grid.shape
    y0, y1 = max(0, fy - horizon), min(H, fy + horizon + 1)
    x0, x1 = max(0, fx - horizon), min(W, fx + horizon + 1)
    patch_known = known[y0:y1, x0:x1]
    patch_grid = grid[y0:y1, x0:x1]
    unknown_free = ((patch_known < 0.5) & (patch_grid < 0.5)).sum()
    # Penalise distance from robot
    d = abs(fx - robot[0]) + abs(fy - robot[1])
    return float(unknown_free) - 0.4 * d


def render(st_ctx=st) -> None:
    explanation_block(
        "C07 — Next-Best-View: Frontier-Based Exploration",
        "When a robot must map an unknown environment, the natural choice of "
        "next viewpoint is one that maximises expected information gain. "
        "DynNav identifies frontier cells (known-free cells adjacent to "
        "unknown cells) and scores each one by an information-gain proxy "
        "(unknown cells visible from there) penalised by traversal cost. "
        "The highest-scoring frontier is the Next Best View.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 8, key="c07_seed")
    size = c2.slider("Grid size", 25, 50, 38, key="c07_size")
    sensor_r = c3.slider("Sensor radius", 3, 12, 6, key="c07_r")
    horizon = c4.slider("Info-gain horizon", 2, 12, 6, key="c07_h")

    grid = make_grid_with_obstacles(size, 14, seed)
    robot = (size // 4, size // 2)
    grid[robot[1], robot[0]] = 0
    known = _build_known_mask(grid, robot, sensor_r)
    frontiers = _frontier_cells(known, grid)
    if not frontiers:
        st.info("No frontiers detected — increase the grid size or change the seed.")
        return

    scored = sorted(
        frontiers,
        key=lambda f: _score_frontier(f, robot, grid, known, horizon),
        reverse=True,
    )
    best = scored[0]
    best_score = _score_frontier(best, robot, grid, known, horizon)
    top5 = scored[:5]

    section_header("Map: known area, frontiers, selected NBV")
    fig = go.Figure()
    # Unknown-as-noise background
    fig.add_trace(go.Heatmap(
        z=1.0 - known, colorscale=[
            [0.0, "rgba(14,17,23,0)"],
            [1.0, "rgba(110,118,129,0.35)"],
        ],
        showscale=False, hoverinfo="skip",
    ))
    fig.add_trace(grid_heatmap_trace(grid))
    # Frontier cells
    fxs = [f[0] for f in frontiers]
    fys = [f[1] for f in frontiers]
    fig.add_trace(go.Scatter(
        x=fxs, y=fys, mode="markers",
        marker=dict(color=COLORS["highlight"], size=6, opacity=0.85),
        name="Frontiers",
    ))
    # Top-5 candidates
    fig.add_trace(go.Scatter(
        x=[t[0] for t in top5], y=[t[1] for t in top5], mode="markers",
        marker=dict(color=COLORS["secondary"], size=12, symbol="diamond",
                    line=dict(color="#0E1117", width=1.5)),
        name="Top-5 NBV candidates",
    ))
    # Best NBV
    fig.add_trace(point_trace(best[0], best[1], COLORS["success"],
                               "Next Best View", symbol="star", size=22))
    # Robot
    fig.add_trace(point_trace(*robot, COLORS["primary"], "Robot",
                               symbol="diamond", size=18))
    square_axes(fig, size)
    st.plotly_chart(apply_theme(fig, height=460), use_container_width=True)

    explored = float(known.mean())
    metrics_row([
        ("Frontier cells", f"{len(frontiers)}", COLORS["highlight"]),
        ("Best NBV score", f"{best_score:.1f}", COLORS["success"]),
        ("Known fraction", f"{explored*100:.1f}%", COLORS["primary"]),
        ("NBV coordinate", f"({best[0]}, {best[1]})", COLORS["secondary"]),
    ])

    interpretation_block(
        "The chosen viewpoint balances information gain (count of "
        "unknown cells revealed) against traversal cost (Manhattan distance "
        "from the robot). Increase the horizon and the planner prefers "
        "distant frontiers that open up large unknown regions; shrink it "
        "and exploration becomes myopic. DynNav cycles through this "
        "selection at each iteration, driving the map-known fraction "
        "towards 1.0."
    )
