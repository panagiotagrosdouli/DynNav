"""C10 — Human-Aware: social-zone-aware path planning."""

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


def _social_field(
    size: int, humans, sigma_intimate: float, sigma_social: float,
    weight_intimate: float, weight_social: float,
) -> np.ndarray:
    """Sum of two Gaussian discomfort fields around each human (intimate + social)."""
    Y, X = np.mgrid[0:size, 0:size]
    field = np.zeros((size, size), dtype=np.float32)
    for hx, hy in humans:
        d2 = (X - hx) ** 2 + (Y - hy) ** 2
        field += weight_intimate * np.exp(-d2 / (2 * sigma_intimate ** 2))
        field += weight_social * np.exp(-d2 / (2 * sigma_social ** 2))
    field = field / max(field.max(), 1e-6)
    return field.astype(np.float32)


def render(st_ctx=st) -> None:
    explanation_block(
        "C10 — Human-Aware Navigation",
        "Mobile robots that share space with people must respect proxemics: "
        "intimate (≈0.45 m), personal (≈1.2 m) and social (≈3.6 m) zones "
        "around each pedestrian. DynNav models these as additive Gaussian "
        "discomfort fields and feeds them to the planner as a soft cost. "
        "The result is a socially compliant path that may be slightly longer "
        "but produces far less discomfort along the way.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 12, key="c10_seed")
    size = c2.slider("Grid size", 25, 50, 35, key="c10_size")
    n_humans = c3.slider("Number of humans", 1, 6, 3, key="c10_h")
    weight = c4.slider("Social weight", 0.0, 8.0, 4.0, 0.2, key="c10_w")
    sigma_s = c5.slider("Social radius σ", 1.0, 6.0, 3.0, 0.2, key="c10_sig")

    grid = make_grid_with_obstacles(size, 10, seed)
    rng = np.random.default_rng(seed + 3)
    humans = []
    for _ in range(n_humans):
        for _ in range(200):
            hx = int(rng.integers(5, size - 5))
            hy = int(rng.integers(5, size - 5))
            if grid[hy, hx] < 0.5 and abs(hx - 2) + abs(hy - 2) > 6:
                humans.append((hx, hy))
                break
    start = (2, 2)
    goal = (size - 3, size - 3)
    grid[start[1], start[0]] = 0
    grid[goal[1], goal[0]] = 0

    social = _social_field(size, humans, 1.0, sigma_s, 1.5, 1.0)
    naive = astar(grid, start, goal)
    social_path = astar(grid, start, goal, risk_field=social, risk_weight=weight)

    def discomfort(path):
        if not path: return 0.0
        return float(np.mean([social[y, x] for x, y in path]))

    d_naive = discomfort(naive["path"])
    d_social = discomfort(social_path["path"])

    section_header("Path comparison")
    cmap, cpan = st.columns([1.5, 1.0], gap="large")
    with cmap:
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=social,
            colorscale=[
                [0.0, "rgba(14,17,23,0)"],
                [0.5, "rgba(245,158,11,0.4)"],
                [1.0, "rgba(239,68,68,0.85)"],
            ],
            showscale=True, colorbar=dict(title="Discomfort", thickness=10, len=0.65),
            hoverinfo="skip", zmin=0.0, zmax=1.0,
        ))
        fig.add_trace(grid_heatmap_trace(grid))
        if naive["success"]:
            fig.add_trace(path_trace(naive["path"], COLORS["primary"],
                                       "Shortest path", width=3))
        if social_path["success"]:
            fig.add_trace(path_trace(social_path["path"], COLORS["secondary"],
                                       "Social-aware path", width=3, dash="dot"))
        for i, (hx, hy) in enumerate(humans):
            fig.add_trace(point_trace(hx, hy, COLORS["danger"],
                                       f"Human {i+1}", symbol="circle", size=16))
        fig.add_trace(point_trace(*start, COLORS["primary"], "Start"))
        fig.add_trace(point_trace(*goal, COLORS["success"], "Goal", symbol="star", size=16))
        square_axes(fig, size)
        st.plotly_chart(apply_theme(fig, height=460), use_container_width=True)

    with cpan:
        section_header("Metrics")
        metrics_row([
            ("Shortest length", f"{naive['cost']:.2f}", COLORS["primary"]),
            ("Social length", f"{social_path['cost']:.2f}", COLORS["secondary"]),
        ])
        st.write("")
        metrics_row([
            ("Shortest discomfort", f"{d_naive:.3f}", COLORS["primary"]),
            ("Social discomfort", f"{d_social:.3f}", COLORS["secondary"]),
        ])
        st.write("")
        reduction = (1.0 - d_social / max(d_naive, 1e-6)) * 100
        metrics_row([
            ("Discomfort reduction", f"{reduction:+.1f}%", COLORS["success"]),
            ("Length penalty",
             f"{(social_path['cost'] - naive['cost']) / max(naive['cost'], 1e-6) * 100:+.1f}%",
             COLORS["text_muted"]),
        ])

    interpretation_block(
        f"The social planner reduced cumulative discomfort by "
        f"<b>{reduction:+.1f}%</b> at a modest length penalty. With higher "
        "social weight, the path may go all the way around groups of "
        "humans; with σ small, only intimate-zone violations matter. "
        "DynNav surfaces both metrics to the supervisor so deployment "
        "in care homes vs. warehouses can be tuned independently."
    )
