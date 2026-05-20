"""C12 — Diffusion Occupancy: predicted future obstacle/risk maps."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS, PLOTLY_RISK_SCALE
from ._common import (
    apply_theme,
    explanation_block,
    interpretation_block,
    metrics_row,
    section_header,
)


def _synthetic_present(size: int, seed: int):
    """Synthetic 'present' occupancy: a few moving obstacles plus velocities."""
    rng = np.random.default_rng(seed)
    obstacles = []
    for _ in range(4):
        obstacles.append({
            "x": float(rng.uniform(4, size - 4)),
            "y": float(rng.uniform(4, size - 4)),
            "vx": float(rng.uniform(-1.5, 1.5)),
            "vy": float(rng.uniform(-1.5, 1.5)),
            "r": float(rng.uniform(1.5, 2.6)),
        })
    return obstacles


def _occupancy_grid(size: int, obstacles, t: float, spread_growth: float) -> np.ndarray:
    """Render Gaussian-blurred occupancy probabilities at time horizon t."""
    Y, X = np.mgrid[0:size, 0:size]
    grid = np.zeros((size, size), dtype=np.float32)
    for o in obstacles:
        px = o["x"] + o["vx"] * t
        py = o["y"] + o["vy"] * t
        sigma = o["r"] + spread_growth * t   # diffusion: variance grows linearly
        grid += np.exp(-((X - px) ** 2 + (Y - py) ** 2) / (2 * sigma ** 2))
    grid = grid / max(grid.max(), 1e-6)
    return grid.astype(np.float32)


def render(st_ctx=st) -> None:
    explanation_block(
        "C12 — Diffusion Occupancy Prediction",
        "DynNav predicts the future occupancy of the environment using a "
        "diffusion-style generative model. The intuition: each obstacle's "
        "future location is uncertain, and that uncertainty grows over time "
        "— modelled here by a Gaussian whose mean shifts with the obstacle's "
        "estimated velocity and whose variance grows linearly with the "
        "prediction horizon. The output is a per-cell probability map of "
        "occupancy at t + Δt, which the planner uses to avoid not just "
        "current obstacles but their probable futures.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 10, key="c12_seed")
    size = c2.slider("Grid size", 25, 50, 35, key="c12_size")
    horizon = c3.slider("Prediction horizon (s)", 0.5, 6.0, 3.0, 0.1, key="c12_t")
    spread = c4.slider("Diffusion spread per second", 0.0, 1.5, 0.45, 0.05, key="c12_s")

    obstacles = _synthetic_present(size, seed)
    now = _occupancy_grid(size, obstacles, 0.0, spread)
    future = _occupancy_grid(size, obstacles, horizon, spread)
    # Build a small time series for animation along a slider
    horizons = [0.0, horizon * 0.33, horizon * 0.66, horizon]
    grids = [_occupancy_grid(size, obstacles, t, spread) for t in horizons]

    section_header("Now vs predicted future occupancy")
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=now, colorscale=PLOTLY_RISK_SCALE, showscale=True,
            colorbar=dict(title="P(occupied)", thickness=10, len=0.7),
            zmin=0.0, zmax=1.0,
        ))
        fig.update_xaxes(scaleanchor="y", scaleratio=1)
        fig.update_layout(title="Current occupancy (t = 0)")
        st.plotly_chart(apply_theme(fig, height=380), use_container_width=True)
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=future, colorscale=PLOTLY_RISK_SCALE, showscale=True,
            colorbar=dict(title="P(occupied)", thickness=10, len=0.7),
            zmin=0.0, zmax=1.0,
        ))
        # Add velocity arrows
        for o in obstacles:
            fx = o["x"] + o["vx"] * horizon
            fy = o["y"] + o["vy"] * horizon
            fig.add_annotation(
                x=fx, y=fy, ax=o["x"], ay=o["y"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowcolor=COLORS["primary"],
                arrowwidth=2,
            )
        fig.update_xaxes(scaleanchor="y", scaleratio=1)
        fig.update_layout(title=f"Predicted occupancy (t = {horizon:.1f} s)")
        st.plotly_chart(apply_theme(fig, height=380), use_container_width=True)

    section_header("Diffusion of uncertainty over horizons")
    means = [float(g.mean()) for g in grids]
    sums = [float((g > 0.5).sum()) for g in grids]
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=horizons, y=means, mode="lines+markers",
        name="Mean occupancy probability",
        line=dict(color=COLORS["secondary"], width=2.5),
    ))
    fig3.add_trace(go.Scatter(
        x=horizons, y=sums, mode="lines+markers",
        name="Cells with P>0.5", yaxis="y2",
        line=dict(color=COLORS["highlight"], width=2.5, dash="dot"),
    ))
    fig3.update_layout(
        xaxis_title="Horizon (s)",
        yaxis=dict(title="Mean P(occupied)", color=COLORS["secondary"]),
        yaxis2=dict(title="Cells P>0.5", overlaying="y", side="right",
                     color=COLORS["highlight"]),
    )
    st.plotly_chart(apply_theme(fig3, height=260), use_container_width=True)

    metrics_row([
        ("Now mean P", f"{now.mean():.3f}", COLORS["primary"]),
        ("Future mean P", f"{future.mean():.3f}", COLORS["secondary"]),
        ("Now risky cells", f"{int((now > 0.5).sum())}", COLORS["primary"]),
        ("Future risky cells", f"{int((future > 0.5).sum())}", COLORS["secondary"]),
    ])

    interpretation_block(
        f"As the horizon extends to {horizon:.1f} s, the diffusion model "
        f"spreads probability across a wider region — risky cells "
        f"(P > 0.5) change from "
        f"{int((now > 0.5).sum())} to {int((future > 0.5).sum())}. "
        "A planner that ignores this future field can collide with a slow-"
        "moving obstacle that is currently clear but will not be at the "
        "moment the robot crosses its path. The diffusion spread parameter "
        "encodes velocity-estimation uncertainty: large values produce "
        "conservative plans."
    )
