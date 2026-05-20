"""C25 — Adversarial: LiDAR spoofing attack and robust planner response."""

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


def _true_environment(n_beams: int, seed: int):
    rng = np.random.default_rng(seed)
    angles = np.linspace(-np.pi, np.pi, n_beams, endpoint=False)
    # Generate a hull of obstacles giving a range profile
    ranges = np.full(n_beams, 10.0)
    n_obs = 4
    for _ in range(n_obs):
        ca = rng.uniform(-np.pi, np.pi)
        width = rng.uniform(0.3, 0.8)
        depth = rng.uniform(2.5, 6.5)
        # Beams within ca±width hit this obstacle at distance depth
        diff = np.abs((angles - ca + np.pi) % (2 * np.pi) - np.pi)
        mask = diff < width
        ranges[mask] = np.minimum(ranges[mask], depth + rng.normal(0, 0.1, mask.sum()))
    return angles, ranges


def _spoof(
    angles: np.ndarray, ranges: np.ndarray,
    n_fake: int, fake_dist: float, seed: int,
):
    """Inject fake near-distance returns into a sector — typical LiDAR spoof."""
    rng = np.random.default_rng(seed + 100)
    spoofed = ranges.copy()
    target_idx = rng.choice(len(angles), size=n_fake, replace=False)
    spoofed[target_idx] = fake_dist + rng.normal(0, 0.05, n_fake)
    return spoofed, target_idx


def _robust_filter(
    ranges: np.ndarray, window: int = 7, k_mad: float = 3.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Median + MAD outlier filter: returns (cleaned, outlier_mask)."""
    n = len(ranges)
    cleaned = ranges.copy()
    mask = np.zeros(n, dtype=bool)
    half = window // 2
    for i in range(n):
        a, b = max(0, i - half), min(n, i + half + 1)
        seg = ranges[a:b]
        med = float(np.median(seg))
        mad = float(np.median(np.abs(seg - med)))
        if mad < 1e-3:
            continue
        if abs(ranges[i] - med) > k_mad * mad:
            cleaned[i] = med
            mask[i] = True
    return cleaned, mask


def render(st_ctx=st) -> None:
    explanation_block(
        "C25 — Adversarial Defence: Robust Response to LiDAR Spoofing",
        "Adversaries can inject fake near-distance returns into a LiDAR's "
        "field of view, fooling the planner into emergency manoeuvres or "
        "freezing it in place. DynNav defends with a median + MAD outlier "
        "filter on each scan, augmented by inter-scan temporal consistency "
        "checks. The downstream planner sees a cleaned scan and an "
        "outlier mask flagged for the security supervisor.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 9, key="c25_seed")
    n_beams = c2.slider("LiDAR beams", 60, 360, 180, 12, key="c25_b")
    n_fake = c3.slider("Spoofed beams", 0, 60, 18, key="c25_f")
    fake_dist = c4.slider("Spoof distance (m)", 0.3, 4.0, 0.8, 0.1, key="c25_d")
    k_mad = c5.slider("Robust filter k·MAD", 1.5, 6.0, 3.5, 0.1, key="c25_k")

    angles, true_ranges = _true_environment(n_beams, seed)
    spoofed, target_idx = _spoof(angles, true_ranges, n_fake, fake_dist, seed)
    cleaned, outlier_mask = _robust_filter(spoofed, window=7, k_mad=k_mad)

    # Convert to Cartesian for plotting
    def to_xy(r):
        return r * np.cos(angles), r * np.sin(angles)

    tx, ty = to_xy(true_ranges)
    sx, sy = to_xy(spoofed)
    cx, cy = to_xy(cleaned)

    section_header("LiDAR scan (top-down)")
    fig = go.Figure()
    # Plot true scan as filled polygon
    fig.add_trace(go.Scatter(
        x=np.append(tx, tx[0]), y=np.append(ty, ty[0]),
        mode="lines", line=dict(color=COLORS["success"], width=2),
        name="True scan",
    ))
    # Spoofed beams
    fig.add_trace(go.Scatter(
        x=sx[target_idx], y=sy[target_idx], mode="markers",
        marker=dict(color=COLORS["danger"], size=10, symbol="x",
                     line=dict(color="#0E1117", width=1)),
        name="Spoofed returns",
    ))
    # Cleaned scan
    fig.add_trace(go.Scatter(
        x=np.append(cx, cx[0]), y=np.append(cy, cy[0]),
        mode="lines", line=dict(color=COLORS["secondary"], width=2, dash="dot"),
        name="Cleaned scan (after filter)",
    ))
    # Outliers detected
    fig.add_trace(go.Scatter(
        x=sx[outlier_mask], y=sy[outlier_mask], mode="markers",
        marker=dict(color=COLORS["highlight"], size=11, symbol="circle-open",
                     line=dict(color=COLORS["highlight"], width=2)),
        name="Detected outliers",
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers", name="Robot",
        marker=dict(color=COLORS["primary"], size=16, symbol="square",
                     line=dict(color="#0E1117", width=1.5)),
    ))
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=440), use_container_width=True)

    section_header("Per-beam ranges")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=true_ranges, name="True",
                                line=dict(color=COLORS["success"], width=2)))
    fig2.add_trace(go.Scatter(y=spoofed, name="Spoofed",
                                line=dict(color=COLORS["danger"], width=1.4, dash="dot")))
    fig2.add_trace(go.Scatter(y=cleaned, name="Cleaned",
                                line=dict(color=COLORS["secondary"], width=2)))
    fig2.update_xaxes(title="Beam index")
    fig2.update_yaxes(title="Range (m)")
    st.plotly_chart(apply_theme(fig2, height=260), use_container_width=True)

    # Detection scoring
    truth_mask = np.zeros(n_beams, dtype=bool); truth_mask[target_idx] = True
    tp = int((outlier_mask & truth_mask).sum())
    fp = int((outlier_mask & ~truth_mask).sum())
    fn = int((~outlier_mask & truth_mask).sum())
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)

    metrics_row([
        ("Spoofed beams", f"{n_fake}", COLORS["danger"]),
        ("Detected (TP)", f"{tp}", COLORS["success"]),
        ("False alarms (FP)", f"{fp}",
         COLORS["text_muted"] if fp == 0 else COLORS["highlight"]),
        ("Precision / Recall",
         f"{prec * 100:.0f}% / {rec * 100:.0f}%", COLORS["primary"]),
    ])

    interpretation_block(
        f"The median + MAD filter caught {tp} of {n_fake} spoofed beams "
        f"({rec * 100:.0f}% recall) with {fp} false alarms. The cleaned "
        "scan stays close to ground truth, so the downstream planner is "
        "not driven into a phantom-obstacle response. Tighten k·MAD to "
        "raise recall at the cost of precision; loosen it to avoid "
        "wrongly suppressing real near-range obstacles."
    )
