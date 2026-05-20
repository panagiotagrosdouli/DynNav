"""C26 — Byzantine Fault-Tolerant Swarm Consensus."""

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


def _simulate_round(
    n_robots: int, n_byzantine: int, true_heading_deg: float,
    honest_noise_deg: float, seed: int,
):
    """Each robot proposes a heading angle.

    Honest robots cluster around true_heading with Gaussian noise. Byzantine
    robots emit arbitrary values designed to skew the mean.
    """
    rng = np.random.default_rng(seed)
    proposals = np.zeros(n_robots)
    honest_idx = np.arange(n_robots - n_byzantine)
    byz_idx = np.arange(n_robots - n_byzantine, n_robots)
    proposals[honest_idx] = (
        true_heading_deg + rng.normal(0, honest_noise_deg, len(honest_idx))
    )
    # Byzantine: extreme outliers
    skew = rng.choice([-1, 1], size=len(byz_idx))
    proposals[byz_idx] = true_heading_deg + skew * rng.uniform(80, 170, len(byz_idx))
    # Wrap to [-180, 180]
    proposals = ((proposals + 180) % 360) - 180
    return proposals, honest_idx, byz_idx


def _trimmed_mean(values: np.ndarray, f: int) -> float:
    """Trim f largest and f smallest, then take the mean — the canonical BFT
    aggregator on 1-D values (Mean-of-Means / α-trimmed)."""
    if 2 * f >= len(values):
        return float(np.median(values))
    sorted_v = np.sort(values)
    trimmed = sorted_v[f:len(values) - f]
    return float(trimmed.mean())


def _coordinate_wise_median(values: np.ndarray) -> float:
    return float(np.median(values))


def render(st_ctx=st) -> None:
    explanation_block(
        "C26 — Byzantine-Fault-Tolerant Swarm Consensus",
        "In a multi-robot swarm, a subset of robots may be compromised, "
        "broken or actively malicious — Byzantine agents that emit "
        "arbitrary proposals. A simple mean is fragile: a single attacker "
        "can move the aggregate arbitrarily far from the truth. DynNav "
        "aggregates proposals with Byzantine-robust estimators (coordinate-"
        "wise median, α-trimmed mean), which tolerate up to <i>f</i> "
        "attackers among <i>n</i> robots provided <i>n &gt; 2f</i>.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 4, key="c26_seed")
    n = c2.slider("Total robots", 5, 25, 12, key="c26_n")
    f_byz = c3.slider("Byzantine robots", 0, 10, 3, key="c26_f")
    noise = c4.slider("Honest noise (deg)", 0.0, 30.0, 6.0, 0.5, key="c26_noise")

    true_heading = 35.0
    f_byz = min(f_byz, max(0, n - 1))
    proposals, honest_idx, byz_idx = _simulate_round(
        n, f_byz, true_heading, noise, seed,
    )

    naive = float(proposals.mean())
    median = _coordinate_wise_median(proposals)
    trimmed = _trimmed_mean(proposals, f_byz)

    section_header("Per-robot proposals on the heading axis")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=proposals[honest_idx], y=np.zeros(len(honest_idx)) + 0.6,
        mode="markers+text",
        marker=dict(color=COLORS["secondary"], size=14, symbol="circle",
                     line=dict(color="#0E1117", width=1.5)),
        text=[f"R{i+1}" for i in honest_idx], textposition="top center",
        textfont=dict(size=9, color=COLORS["text_muted"]),
        name="Honest robots", hoverinfo="text",
    ))
    fig.add_trace(go.Scatter(
        x=proposals[byz_idx], y=np.zeros(len(byz_idx)) - 0.6,
        mode="markers+text",
        marker=dict(color=COLORS["danger"], size=16, symbol="x",
                     line=dict(color="#0E1117", width=1.5)),
        text=[f"R{i+1}" for i in byz_idx], textposition="bottom center",
        textfont=dict(size=9, color=COLORS["text_muted"]),
        name="Byzantine robots", hoverinfo="text",
    ))
    # Aggregator lines
    fig.add_vline(x=true_heading, line_color=COLORS["success"], line_dash="solid",
                   annotation_text="Ground truth", annotation_position="top")
    fig.add_vline(x=naive, line_color=COLORS["danger"], line_dash="dot",
                   annotation_text="Naive mean", annotation_position="bottom")
    fig.add_vline(x=median, line_color=COLORS["primary"], line_dash="dash",
                   annotation_text="Median", annotation_position="top")
    fig.add_vline(x=trimmed, line_color=COLORS["highlight"], line_dash="dashdot",
                   annotation_text="α-trimmed mean", annotation_position="bottom")
    fig.update_xaxes(title="Proposed heading (deg)", range=[-185, 185])
    fig.update_yaxes(visible=False, range=[-1.5, 1.5])
    st.plotly_chart(apply_theme(fig, height=360), use_container_width=True)

    section_header("Aggregator error versus ground truth")
    err_naive = abs(naive - true_heading)
    err_median = abs(median - true_heading)
    err_trim = abs(trimmed - true_heading)
    fig2 = go.Figure(go.Bar(
        x=["Naive mean", "Coordinate-wise median", "α-trimmed mean"],
        y=[err_naive, err_median, err_trim],
        marker_color=[COLORS["danger"], COLORS["primary"], COLORS["highlight"]],
        text=[f"{err_naive:.1f}°", f"{err_median:.1f}°", f"{err_trim:.1f}°"],
        textposition="auto",
    ))
    fig2.update_yaxes(title="Absolute heading error (deg)")
    st.plotly_chart(apply_theme(fig2, height=300), use_container_width=True)

    safe = n > 2 * f_byz
    metrics_row([
        ("Total robots", f"{n}", COLORS["primary"]),
        ("Byzantine f", f"{f_byz}", COLORS["danger"]),
        ("BFT condition n > 2f",
         "SATISFIED" if safe else "VIOLATED",
         COLORS["success"] if safe else COLORS["danger"]),
        ("Median error", f"{err_median:.1f}°",
         COLORS["success"] if err_median < 15 else COLORS["highlight"]),
    ])

    interpretation_block(
        f"With n={n} and f={f_byz}, the BFT safety condition n > 2f is "
        f"{'satisfied' if safe else 'violated'}. The naive mean is "
        f"corrupted by {err_naive:.1f}°, while the coordinate-wise median "
        f"and α-trimmed mean keep the aggregate within "
        f"{max(err_median, err_trim):.1f}° of ground truth. Push f past "
        "n/2 and even robust estimators lose their guarantees — at that "
        "point DynNav must escalate to identity-checked voting rather "
        "than anonymous aggregation."
    )
