"""C03 — CVaR A*: shortest path vs risk-aware path on a risk map."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS, PLOTLY_RISK_SCALE
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


def _build_risk_field(size: int, grid: np.ndarray, seed: int) -> np.ndarray:
    """Synthetic risk field: high near obstacles, plus Gaussian risk peaks."""
    rng = np.random.default_rng(seed + 999)
    Y, X = np.mgrid[0:size, 0:size]
    risk = np.zeros((size, size), dtype=np.float32)
    # Risk peaks
    n_peaks = 4
    for _ in range(n_peaks):
        cx, cy = rng.uniform(3, size - 3), rng.uniform(3, size - 3)
        s = rng.uniform(2.0, 4.0)
        risk += np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * s ** 2))
    # Inflate around obstacles
    pad = 2
    H = grid.shape[0]
    obstacle_neighborhood = np.zeros_like(grid)
    for dy in range(-pad, pad + 1):
        for dx in range(-pad, pad + 1):
            r = np.sqrt(dx * dx + dy * dy)
            if r > pad:
                continue
            shifted = np.roll(np.roll(grid, dy, axis=0), dx, axis=1)
            obstacle_neighborhood = np.maximum(
                obstacle_neighborhood, shifted * (1.0 - r / (pad + 1))
            )
    risk = risk + obstacle_neighborhood * 1.5
    risk = risk / max(risk.max(), 1e-6)
    risk[grid > 0.5] = 1.0
    return risk.astype(np.float32)


def _cvar(values, alpha: float) -> float:
    if not values:
        return 0.0
    arr = np.sort(np.asarray(values))
    k = max(1, int(np.ceil((1 - alpha) * len(arr))))
    return float(arr[-k:].mean())


def render(st_ctx=st) -> None:
    explanation_block(
        "C03 — CVaR A*: Risk-Sensitive Path Planning",
        "Conditional Value-at-Risk (CVaR) measures the expected loss in the "
        "worst α-fraction of outcomes — a coherent risk measure widely used "
        "in finance and recently in safe robotics. CVaR A* augments the edge "
        "cost with a tail-risk penalty, so the planner avoids paths that are "
        "short on average but expose the robot to high worst-case risk. "
        "This trades a small length increase for a large reduction in "
        "collision likelihood under uncertain perception.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 7, key="c03_seed")
    size = c2.slider("Grid size", 20, 50, 35, key="c03_size")
    n_obs = c3.slider("Obstacles", 5, 25, 14, key="c03_obs")
    rw = c4.slider("Risk weight", 0.0, 6.0, 3.0, 0.1, key="c03_w")
    alpha = c5.slider("CVaR α", 0.80, 0.99, 0.95, 0.01, key="c03_a")

    grid = make_grid_with_obstacles(size, n_obs, seed)
    start = (2, 2)
    goal = (size - 3, size - 3)
    grid[start[1], start[0]] = 0
    grid[goal[1], goal[0]] = 0
    risk = _build_risk_field(size, grid, seed)

    short = astar(grid, start, goal)
    safe = astar(grid, start, goal, risk_field=risk, risk_weight=rw)

    def risks_along(path):
        return [float(risk[y, x]) for x, y in path] if path else []

    r_short = risks_along(short["path"])
    r_safe = risks_along(safe["path"])

    section_header("Risk map and planned paths")
    cmap, cpan = st.columns([1.5, 1.0], gap="large")
    with cmap:
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=risk, colorscale=PLOTLY_RISK_SCALE, showscale=True,
            colorbar=dict(title="Risk", thickness=12, len=0.7),
            hoverinfo="skip", zmin=0.0, zmax=1.0,
        ))
        fig.add_trace(grid_heatmap_trace(grid))
        if short["success"]:
            fig.add_trace(path_trace(short["path"], COLORS["primary"], "Shortest path", width=3.0))
        if safe["success"]:
            fig.add_trace(path_trace(safe["path"], COLORS["secondary"], "CVaR risk-aware", width=3.0, dash="dot"))
        fig.add_trace(point_trace(*start, COLORS["primary"], "Start"))
        fig.add_trace(point_trace(*goal, COLORS["success"], "Goal", symbol="star", size=16))
        square_axes(fig, size)
        st.plotly_chart(apply_theme(fig, height=460), use_container_width=True)

    with cpan:
        section_header("Metrics")
        len_s = short["cost"] if short["success"] else float("nan")
        len_r = safe["cost"] if safe["success"] else float("nan")
        avg_s = float(np.mean(r_short)) if r_short else 0.0
        avg_r = float(np.mean(r_safe)) if r_safe else 0.0
        cvar_s = _cvar(r_short, alpha)
        cvar_r = _cvar(r_safe, alpha)
        metrics_row([
            ("Shortest length", f"{len_s:.2f}", COLORS["primary"]),
            ("Risk-aware length", f"{len_r:.2f}", COLORS["secondary"]),
        ])
        st.write("")
        metrics_row([
            ("Shortest avg risk", f"{avg_s:.3f}", COLORS["primary"]),
            ("Risk-aware avg risk", f"{avg_r:.3f}", COLORS["secondary"]),
        ])
        st.write("")
        metrics_row([
            (f"Shortest CVaR α={alpha:.2f}", f"{cvar_s:.3f}", COLORS["primary"]),
            (f"Risk-aware CVaR α={alpha:.2f}", f"{cvar_r:.3f}", COLORS["secondary"]),
        ])

    # Per-step risk profile
    section_header("Per-step risk along each path")
    fig2 = go.Figure()
    if r_short:
        fig2.add_trace(go.Scatter(
            y=r_short, mode="lines", name="Shortest",
            line=dict(color=COLORS["primary"], width=2),
        ))
    if r_safe:
        fig2.add_trace(go.Scatter(
            y=r_safe, mode="lines", name="Risk-aware",
            line=dict(color=COLORS["secondary"], width=2, dash="dot"),
        ))
    fig2.add_hline(
        y=cvar_s, line_color=COLORS["primary"], line_dash="dash",
        annotation_text=f"CVaR (shortest)", annotation_position="right",
    )
    fig2.add_hline(
        y=cvar_r, line_color=COLORS["secondary"], line_dash="dash",
        annotation_text=f"CVaR (risk-aware)", annotation_position="right",
    )
    fig2.update_yaxes(title="Risk", range=[0, 1.05])
    fig2.update_xaxes(title="Step")
    st.plotly_chart(apply_theme(fig2, height=260), use_container_width=True)

    delta_len_pct = (len_r - len_s) / max(len_s, 1e-6) * 100.0
    delta_cvar_pct = (cvar_r - cvar_s) / max(cvar_s, 1e-6) * 100.0
    interpretation_block(
        f"The CVaR-aware planner traded <b>{delta_len_pct:+.1f}%</b> path "
        f"length for <b>{delta_cvar_pct:+.1f}%</b> change in tail risk at "
        f"α = {alpha:.2f}. Slide the risk weight to 0 to recover the standard "
        "shortest path; large weights collapse the route onto the very lowest-"
        "risk corridor, which can become circuitous. This is exactly the "
        "trade-off DynNav exposes to the safety supervisor at run time."
    )
