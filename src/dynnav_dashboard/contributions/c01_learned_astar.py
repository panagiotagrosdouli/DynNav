"""C01 — Learned A*: vanilla A* vs a learned heuristic."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS
from ._common import (
    apply_theme,
    astar,
    explanation_block,
    grid_heatmap_trace,
    interpretation_block,
    make_grid_with_obstacles,
    metrics_row,
    path_trace,
    point_trace,
    section_header,
    square_axes,
)


def _learned_heuristic_field(size: int, goal, grid: np.ndarray) -> np.ndarray:
    """Synthesise a 'learned' heuristic bias.

    A production system would train a CNN on optimal cost-to-go labels. Here
    we approximate that signal with a Chebyshev distance-to-nearest-obstacle
    map computed by iterative dilation: cells inside dense clutter receive a
    higher heuristic bias, capturing the intuition a learned model picks up
    — namely that clutter inflates effective travel distance.
    """
    H, W = grid.shape
    # Iterative Chebyshev distance transform (pure NumPy).
    INF = float(H + W)
    dist = np.where(grid > 0.5, 0.0, INF).astype(np.float32)
    for _ in range(max(H, W)):
        shifted = np.stack([
            np.pad(dist, ((1, 0), (0, 0)), constant_values=INF)[:-1, :],
            np.pad(dist, ((0, 1), (0, 0)), constant_values=INF)[1:, :],
            np.pad(dist, ((0, 0), (1, 0)), constant_values=INF)[:, :-1],
            np.pad(dist, ((0, 0), (0, 1)), constant_values=INF)[:, 1:],
        ])
        new_dist = np.minimum(dist, shifted.min(axis=0) + 1.0)
        if np.allclose(new_dist, dist):
            break
        dist = new_dist
    bias = 1.0 / (dist + 1.0)
    bias = bias / max(bias.max(), 1e-6) * 1.2
    return bias.astype(np.float32)


def render(st_ctx=st) -> None:
    explanation_block(
        "C01 — Learned A*: Heuristic Guidance from Data",
        "Classical A* relies on hand-crafted admissible heuristics such as "
        "Euclidean or octile distance. A learned heuristic, trained on "
        "optimal cost-to-go labels from a dataset of solved planning problems, "
        "biases the search toward goal-reaching directions in cluttered "
        "environments. This typically reduces the number of node expansions "
        "at the cost of a small loss in optimality and a strict admissibility "
        "guarantee — a trade-off acceptable in many robotics settings.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Random seed", 0, 50, 4, key="c01_seed")
    size = c2.slider("Grid size", 20, 50, 35, key="c01_size")
    n_obs = c3.slider("Obstacles", 5, 30, 18, key="c01_obs")
    weight = c4.slider(
        "Learned heuristic weight",
        0.0, 2.0, 1.0, 0.05,
        key="c01_w",
        help="0 = vanilla A*, larger = more aggressive learned bias.",
    )

    grid = make_grid_with_obstacles(size, n_obs, seed)
    start = (2, 2)
    goal = (size - 3, size - 3)
    # Ensure start and goal are clear
    grid[start[1], start[0]] = 0
    grid[goal[1], goal[0]] = 0

    vanilla = astar(grid, start, goal)
    bias = _learned_heuristic_field(size, goal, grid) * weight
    learned = astar(grid, start, goal, heuristic_field=bias)

    section_header("Search comparison")
    cmap, cpan = st.columns([1.4, 1.0], gap="large")

    with cmap:
        fig = go.Figure()
        fig.add_trace(grid_heatmap_trace(grid))
        # Heuristic field as faint backdrop
        fig.add_trace(
            go.Heatmap(
                z=bias,
                colorscale=[
                    [0.0, "rgba(167,139,250,0.0)"],
                    [1.0, "rgba(167,139,250,0.45)"],
                ],
                showscale=False,
                hoverinfo="skip",
            )
        )
        if vanilla["success"]:
            fig.add_trace(
                path_trace(vanilla["path"], COLORS["primary"], "Vanilla A*", width=3.5)
            )
        if learned["success"]:
            fig.add_trace(
                path_trace(
                    learned["path"], COLORS["secondary"], "Learned A*",
                    width=3.5, dash="dot",
                )
            )
        fig.add_trace(point_trace(*start, COLORS["primary"], "Start"))
        fig.add_trace(point_trace(*goal, COLORS["success"], "Goal", symbol="star", size=16))
        square_axes(fig, size)
        st.plotly_chart(apply_theme(fig, height=440), use_container_width=True)

    with cpan:
        section_header("Metrics")
        exp_v = vanilla["expansions"]
        exp_l = learned["expansions"]
        cost_v = vanilla["cost"] if vanilla["success"] else float("nan")
        cost_l = learned["cost"] if learned["success"] else float("nan")
        reduction = (
            100.0 * (exp_v - exp_l) / max(exp_v, 1) if exp_v else 0.0
        )
        metrics_row([
            ("Vanilla expansions", f"{exp_v}", COLORS["primary"]),
            ("Learned expansions", f"{exp_l}", COLORS["secondary"]),
        ])
        st.write("")
        metrics_row([
            ("Vanilla cost", f"{cost_v:.2f}", COLORS["primary"]),
            ("Learned cost", f"{cost_l:.2f}", COLORS["secondary"]),
        ])
        st.write("")
        metrics_row([
            (
                "Expansion reduction",
                f"{reduction:+.1f}%",
                COLORS["success"] if reduction > 0 else COLORS["danger"],
            ),
            (
                "Cost overhead",
                f"{(cost_l - cost_v):+.2f}",
                COLORS["text_muted"],
            ),
        ])

    interpretation_block(
        f"On this instance, the learned heuristic reduced node expansions by "
        f"<b>{reduction:+.1f}%</b> while changing path cost by "
        f"<b>{(cost_l - cost_v):+.2f}</b>. In dense clutter the learned bias "
        "pays off most; in open space the two planners behave identically. "
        "Slide the weight to 0 to recover vanilla A* exactly, and observe "
        "how excessive weights start to inflate cost as admissibility is lost."
    )
