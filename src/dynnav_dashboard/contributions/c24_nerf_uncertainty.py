"""C24 — NeRF Uncertainty: uncertainty field over an unexplored scene."""

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
    point_trace,
    section_header,
    square_axes,
)


def _uncertainty_field(
    size: int, cam_positions: np.ndarray, cam_radii: np.ndarray,
    base_unc: float, decay: float,
):
    """Per-cell uncertainty: high far from any camera viewpoint, decays as
    1 / (1 + decay * d) near observed viewpoints."""
    Y, X = np.mgrid[0:size, 0:size]
    base = np.full((size, size), base_unc, dtype=np.float32)
    coverage = np.zeros((size, size), dtype=np.float32)
    for (cx, cy), r in zip(cam_positions, cam_radii):
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        # exponential coverage falloff
        contrib = np.exp(-d / r) * 1.0
        coverage = np.maximum(coverage, contrib)
    field = base * (1.0 - coverage)
    field = np.clip(field, 0.0, 1.0)
    return field, coverage


def render(st_ctx=st) -> None:
    explanation_block(
        "C24 — NeRF Uncertainty: Quantifying What the Map Does Not Know",
        "Neural Radiance Fields render novel views by integrating a learned "
        "density and colour function along camera rays. Crucially, an "
        "ensemble or Bayesian NeRF can produce a calibrated uncertainty "
        "field over space — high where no training viewpoint observed the "
        "region. DynNav uses this field to direct exploration: the next "
        "viewpoint is chosen to maximise uncertainty reduction, much like "
        "C07's frontier exploration but in a continuous photometric "
        "representation.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 7, key="c24_seed")
    size = c2.slider("Grid size", 30, 60, 40, key="c24_size")
    n_cams = c3.slider("Observed viewpoints", 1, 12, 5, key="c24_c")
    cam_r = c4.slider("Per-camera coverage radius", 2.0, 12.0, 5.5, 0.5, key="c24_r")

    rng = np.random.default_rng(seed)
    cam_xy = rng.uniform(3, size - 3, (n_cams, 2))
    radii = np.full(n_cams, cam_r)
    field, coverage = _uncertainty_field(
        size, cam_xy, radii, base_unc=1.0, decay=1.0,
    )

    # Suggest next best viewpoint: argmax over remaining uncertainty
    flat_idx = int(np.argmax(field))
    by, bx = np.unravel_index(flat_idx, field.shape)

    section_header("Uncertainty heatmap with camera locations")
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=field, colorscale=PLOTLY_RISK_SCALE,
        showscale=True, colorbar=dict(title="Uncertainty", thickness=10, len=0.7),
        zmin=0.0, zmax=1.0,
    ))
    # Cameras
    fig.add_trace(go.Scatter(
        x=cam_xy[:, 0], y=cam_xy[:, 1], mode="markers+text",
        marker=dict(color=COLORS["secondary"], size=14, symbol="diamond",
                     line=dict(color="#0E1117", width=1.5)),
        text=[f"C{i+1}" for i in range(n_cams)], textposition="top center",
        textfont=dict(size=10, color=COLORS["text"]),
        name="Observed viewpoints",
    ))
    # Coverage rings (1/e radius)
    theta = np.linspace(0, 2 * np.pi, 80)
    for cx, cy in cam_xy:
        fig.add_trace(go.Scatter(
            x=cx + cam_r * np.cos(theta), y=cy + cam_r * np.sin(theta),
            mode="lines", line=dict(color=COLORS["secondary"], width=1, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ))
    # Next best
    fig.add_trace(point_trace(bx, by, COLORS["highlight"],
                               "Next-best viewpoint", symbol="star", size=22))
    square_axes(fig, size)
    st.plotly_chart(apply_theme(fig, height=480), use_container_width=True)

    section_header("Histogram of per-cell uncertainty")
    fig2 = go.Figure(go.Histogram(
        x=field.flatten(), nbinsx=30,
        marker_color=COLORS["secondary"], opacity=0.85,
    ))
    fig2.update_xaxes(title="Uncertainty value", range=[0, 1.05])
    fig2.update_yaxes(title="Cells")
    st.plotly_chart(apply_theme(fig2, height=240), use_container_width=True)

    mean_u = float(field.mean())
    max_u = float(field.max())
    well_covered = float((field < 0.2).mean()) * 100
    metrics_row([
        ("Mean uncertainty", f"{mean_u:.3f}", COLORS["secondary"]),
        ("Max uncertainty", f"{max_u:.3f}", COLORS["highlight"]),
        ("Well-covered cells (<0.2)", f"{well_covered:.0f}%", COLORS["success"]),
        ("Next-best viewpoint", f"({bx}, {by})", COLORS["highlight"]),
    ])

    interpretation_block(
        f"With {n_cams} observed viewpoints and a per-camera coverage radius "
        f"of {cam_r:.1f}, {well_covered:.0f}% of the scene is well covered "
        "(uncertainty below 0.2). The suggested next-best viewpoint sits "
        "at the field's argmax — capturing it would, in expectation, "
        "reduce uncertainty across the largest uncovered region. In a real "
        "NeRF pipeline this query is performed with an ensemble variance "
        "estimate or with a learned uncertainty head."
    )
