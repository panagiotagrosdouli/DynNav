"""C23 — Gaussian Splatting: 3D scene reconstruction style visualisation."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS
from ._common import (
    apply_theme,
    explanation_block,
    interpretation_block,
    metrics_row,
    section_header,
)


def _synthesise_scene(n_splats: int, complexity: float, seed: int):
    """Generate 3D Gaussian 'splats' shaped like a small indoor scene.

    Each splat has a 3D position, an anisotropic scale and a base colour. The
    scene is composed of: a floor plane, two vertical walls, a 'table' box,
    and a 'lamp' cluster — enough to give a recognisable 3DGS feel.
    """
    rng = np.random.default_rng(seed)
    pts: list[np.ndarray] = []
    colors: list[np.ndarray] = []
    sizes: list[float] = []

    # Floor
    n_floor = int(n_splats * 0.35)
    x = rng.uniform(-4, 4, n_floor)
    y = rng.uniform(-4, 4, n_floor)
    z = rng.normal(0, 0.05, n_floor)
    pts.append(np.stack([x, y, z], axis=1))
    floor_c = np.tile(np.array([90, 110, 130]), (n_floor, 1)) + rng.integers(-10, 10, (n_floor, 3))
    colors.append(floor_c)
    sizes.extend([4.5] * n_floor)

    # Walls
    n_wall = int(n_splats * 0.18)
    xw = rng.uniform(-4, 4, n_wall)
    yw = np.full(n_wall, -3.8) + rng.normal(0, 0.08, n_wall)
    zw = rng.uniform(0, 3, n_wall)
    pts.append(np.stack([xw, yw, zw], axis=1))
    colors.append(np.tile(np.array([130, 140, 160]), (n_wall, 1)) + rng.integers(-15, 15, (n_wall, 3)))
    sizes.extend([5.0] * n_wall)
    xw2 = np.full(n_wall, -3.8) + rng.normal(0, 0.08, n_wall)
    yw2 = rng.uniform(-4, 4, n_wall)
    zw2 = rng.uniform(0, 3, n_wall)
    pts.append(np.stack([xw2, yw2, zw2], axis=1))
    colors.append(np.tile(np.array([100, 120, 150]), (n_wall, 1)) + rng.integers(-10, 10, (n_wall, 3)))
    sizes.extend([5.0] * n_wall)

    # Table top + legs
    n_table = int(n_splats * 0.15)
    xt = rng.uniform(0.5, 2.5, n_table)
    yt = rng.uniform(-1.5, 0.0, n_table)
    zt = rng.uniform(0.95, 1.1, n_table)
    pts.append(np.stack([xt, yt, zt], axis=1))
    colors.append(np.tile(np.array([200, 160, 110]), (n_table, 1)) + rng.integers(-10, 10, (n_table, 3)))
    sizes.extend([5.5] * n_table)

    # Lamp (a glowing cluster)
    n_lamp = int(n_splats * 0.10)
    xl = rng.normal(1.5, 0.18, n_lamp)
    yl = rng.normal(-1.0, 0.18, n_lamp)
    zl = rng.normal(2.2, 0.25, n_lamp)
    pts.append(np.stack([xl, yl, zl], axis=1))
    colors.append(np.tile(np.array([255, 220, 130]), (n_lamp, 1)) + rng.integers(-10, 10, (n_lamp, 3)))
    sizes.extend([8.0] * n_lamp)

    # Background clutter (controls complexity)
    n_clut = int(n_splats * 0.22 * (0.4 + 0.6 * complexity))
    xc = rng.uniform(-4, 4, n_clut)
    yc = rng.uniform(-4, 4, n_clut)
    zc = rng.uniform(0.05, 3.0, n_clut)
    pts.append(np.stack([xc, yc, zc], axis=1))
    colors.append(np.tile(np.array([160, 170, 180]), (n_clut, 1)) + rng.integers(-30, 30, (n_clut, 3)))
    sizes.extend([3.5] * n_clut)

    P = np.concatenate(pts, axis=0)
    C = np.concatenate(colors, axis=0)
    C = np.clip(C, 0, 255).astype(int)
    S = np.array(sizes)
    return P, C, S


def render(st_ctx=st) -> None:
    explanation_block(
        "C23 — Gaussian Splatting: Reconstructive 3D Scene Representation",
        "3D Gaussian Splatting (3DGS) represents a scene as a soup of "
        "anisotropic 3D Gaussians, each with a position, scale, rotation, "
        "opacity and view-dependent colour. Rendering is fast and "
        "differentiable, so the model can be optimised from posed images "
        "without a triangle mesh. DynNav can use 3DGS as a high-fidelity "
        "memory representation for re-localisation and offline analysis.",
    )

    section_header("Interactive controls")
    c1, c2, c3 = st.columns(3)
    seed = c1.slider("Seed", 0, 50, 12, key="c23_seed")
    n_splats = c2.slider("Number of splats", 500, 6000, 2400, 100, key="c23_n")
    complexity = c3.slider("Scene complexity", 0.0, 1.0, 0.5, 0.05, key="c23_c")

    P, C, S = _synthesise_scene(n_splats, complexity, seed)
    colorscale = [f"rgb({c[0]},{c[1]},{c[2]})" for c in C]

    section_header("Reconstructed scene (rotate / zoom in 3D)")
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=P[:, 0], y=P[:, 1], z=P[:, 2],
        mode="markers",
        marker=dict(
            size=S,
            color=colorscale,
            opacity=0.75,
            line=dict(width=0),
        ),
        hoverinfo="skip",
    ))
    fig.update_scenes(
        xaxis=dict(showbackground=False, color=COLORS["text"], gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(showbackground=False, color=COLORS["text"], gridcolor="rgba(255,255,255,0.08)"),
        zaxis=dict(showbackground=False, color=COLORS["text"], gridcolor="rgba(255,255,255,0.08)"),
        aspectmode="data",
        bgcolor=COLORS["bg"],
    )
    fig.update_layout(
        height=540, margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor=COLORS["bg"],
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2D top-down density
    section_header("Top-down density (occupancy footprint)")
    H, _, _ = np.histogram2d(P[:, 0], P[:, 1], bins=40, range=[[-4, 4], [-4, 4]])
    fig2 = go.Figure(go.Heatmap(
        z=H.T, colorscale=[
            [0.0, "rgba(14,17,23,0)"],
            [0.5, "rgba(34,211,238,0.5)"],
            [1.0, "rgba(167,139,250,1.0)"],
        ],
        showscale=True, colorbar=dict(title="Splats / cell", thickness=10, len=0.7),
    ))
    fig2.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig2, height=320), use_container_width=True)

    metrics_row([
        ("Splats", f"{len(P):,}", COLORS["primary"]),
        ("Footprint cells (>0)",
         f"{int((H > 0).sum())}", COLORS["secondary"]),
        ("Mean splat height",
         f"{P[:, 2].mean():.2f} m", COLORS["highlight"]),
        ("Scene complexity index",
         f"{complexity:.2f}", COLORS["accent"]),
    ])

    interpretation_block(
        f"This synthetic scene uses {len(P):,} Gaussian primitives to "
        "represent a floor, two walls, a table and a lamp. In a real "
        "3DGS pipeline each primitive is differentiable so the parameters "
        "(position, scale, colour, opacity) are optimised against posed "
        "images. DynNav benefits from the photorealistic rendering for "
        "high-fidelity localisation but the dashboard exposes only the "
        "geometry — the actual rendering happens on GPU off-line."
    )
