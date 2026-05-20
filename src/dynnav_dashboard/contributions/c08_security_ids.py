"""C08 — Security IDS: chi-square / CUSUM anomaly detection on sensor stream."""

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


def _generate_stream(n: int, attack_strength: float, seed: int):
    rng = np.random.default_rng(seed)
    base = rng.normal(loc=0.0, scale=1.0, size=n)
    label = np.zeros(n, dtype=int)
    # Two attack windows
    s1, e1 = int(n * 0.30), int(n * 0.42)
    s2, e2 = int(n * 0.62), int(n * 0.78)
    base[s1:e1] += attack_strength * (1.0 + 0.4 * np.sin(np.linspace(0, 3, e1 - s1)))
    base[s2:e2] += attack_strength * 0.6
    label[s1:e1] = 1
    label[s2:e2] = 1
    return base, label


def _chi_square(stream: np.ndarray, window: int):
    """χ²-style residual-energy detector over a sliding window."""
    n = len(stream)
    stat = np.zeros(n)
    for k in range(n):
        a, b = max(0, k - window + 1), k + 1
        seg = stream[a:b]
        stat[k] = float(np.sum(seg ** 2))
    return stat


def _cusum(stream: np.ndarray, drift: float):
    """Standard CUSUM (positive-side)."""
    n = len(stream)
    s = np.zeros(n)
    for k in range(1, n):
        s[k] = max(0.0, s[k - 1] + (stream[k] - drift))
    return s


def render(st_ctx=st) -> None:
    explanation_block(
        "C08 — Security IDS: Anomaly Detection on Sensor Streams",
        "Robots are increasingly targeted by sensor-level attacks — LiDAR "
        "spoofing, GPS jamming, replayed wheel-encoder data. DynNav runs a "
        "lightweight intrusion-detection layer on each sensor stream: a "
        "χ²-style residual-energy test over a sliding window flags burst "
        "anomalies, and CUSUM accumulates small persistent biases that a "
        "windowed test alone would miss.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 6, key="c08_seed")
    n = c2.slider("Stream length", 200, 800, 500, 20, key="c08_n")
    strength = c3.slider("Attack strength σ", 0.5, 5.0, 2.2, 0.1, key="c08_s")
    win = c4.slider("χ² window", 5, 60, 20, key="c08_w")
    th_chi = c5.slider("χ² threshold", 5.0, 200.0, 60.0, 1.0, key="c08_t")

    stream, label = _generate_stream(n, strength, seed)
    chi = _chi_square(stream, win)
    cu = _cusum(stream, drift=0.2)
    th_cu = max(8.0, 0.04 * n)

    fired_chi = chi > th_chi
    fired_cu = cu > th_cu
    fired_any = fired_chi | fired_cu
    tp = int((fired_any & (label == 1)).sum())
    fp = int((fired_any & (label == 0)).sum())
    fn = int((~fired_any & (label == 1)).sum())
    tn = int((~fired_any & (label == 0)).sum())
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-9)

    section_header("Raw sensor stream with ground-truth attack windows")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=stream, mode="lines", name="Sensor reading",
        line=dict(color=COLORS["accent"], width=1.2),
    ))
    # Highlight attack windows
    starts = np.where(np.diff(np.r_[0, label, 0]) == 1)[0]
    ends = np.where(np.diff(np.r_[0, label, 0]) == -1)[0] - 1
    for s, e in zip(starts, ends):
        fig.add_vrect(x0=s, x1=e, fillcolor=COLORS["danger"],
                       opacity=0.12, line_width=0, layer="below")
    fig.update_yaxes(title="Sensor value")
    fig.update_xaxes(title="Sample")
    st.plotly_chart(apply_theme(fig, height=260), use_container_width=True)

    section_header("Detectors")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=chi, name="χ² statistic", mode="lines",
                                line=dict(color=COLORS["primary"], width=2)))
    fig2.add_trace(go.Scatter(y=cu, name="CUSUM", mode="lines",
                                line=dict(color=COLORS["secondary"], width=2, dash="dot"),
                                yaxis="y2"))
    fig2.add_hline(y=th_chi, line_color=COLORS["primary"], line_dash="dash",
                    annotation_text="χ² threshold", annotation_position="right")
    fig2.add_hline(y=th_cu, line_color=COLORS["secondary"], line_dash="dash",
                    annotation_text="CUSUM threshold", annotation_position="right",
                    annotation_yref="y2")
    fig2.update_layout(
        yaxis=dict(title="χ²", color=COLORS["primary"]),
        yaxis2=dict(title="CUSUM", overlaying="y", side="right",
                     color=COLORS["secondary"]),
    )
    fig2.update_xaxes(title="Sample")
    st.plotly_chart(apply_theme(fig2, height=260), use_container_width=True)

    metrics_row([
        ("Detected (TP)", f"{tp}", COLORS["success"]),
        ("False alarms (FP)", f"{fp}", COLORS["danger"]),
        ("Precision", f"{prec*100:.1f}%", COLORS["primary"]),
        ("Recall", f"{rec*100:.1f}%", COLORS["primary"]),
        ("F1", f"{f1*100:.1f}%", COLORS["secondary"]),
    ])

    interpretation_block(
        f"Under this attack strength (σ={strength:.1f}), the joint χ² / CUSUM "
        f"detector achieved F1 = {f1*100:.1f}% (precision {prec*100:.1f}%, "
        f"recall {rec*100:.1f}%). χ² is fast to react to bursts; CUSUM "
        "catches the slow, low-amplitude bias in the second window. Both "
        "are O(1) per sample — cheap enough to run on the safety MCU "
        "alongside DynNav's main pipeline."
    )
