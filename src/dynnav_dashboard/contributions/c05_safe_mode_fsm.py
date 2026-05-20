"""C05 — Safe-Mode FSM: risk-driven mode and speed control."""

from __future__ import annotations

import numpy as np
import pandas as pd
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


# Mode definitions: thresholds operate on risk in [0, 1]
MODES = [
    ("NOMINAL",   0.00, 0.30, 1.00, COLORS["success"]),
    ("CAUTIOUS",  0.30, 0.55, 0.65, COLORS["secondary"]),
    ("DEGRADED",  0.55, 0.80, 0.35, COLORS["highlight"]),
    ("EMERGENCY", 0.80, 1.01, 0.00, COLORS["danger"]),
]


def _mode_for(risk: float, hysteresis: float, prev_mode: str) -> tuple[str, float, str]:
    """Return (mode_name, speed_scale, color), honouring hysteresis."""
    # First check the current mode's exit bands with hysteresis
    for name, lo, hi, scale, color in MODES:
        if name == prev_mode:
            # Stay in current mode if within widened band
            if (lo - hysteresis) <= risk < (hi + hysteresis):
                return name, scale, color
            break
    # Otherwise jump to whichever band the risk lives in
    for name, lo, hi, scale, color in MODES:
        if lo <= risk < hi:
            return name, scale, color
    return MODES[-1][0], MODES[-1][3], MODES[-1][4]


def render(st_ctx=st) -> None:
    explanation_block(
        "C05 — Safe-Mode FSM: Graceful Degradation under Risk",
        "Real robots cannot operate in a single mode regardless of "
        "perceived risk. DynNav uses a finite-state machine with NOMINAL → "
        "CAUTIOUS → DEGRADED → EMERGENCY transitions driven by a fused risk "
        "signal. Each mode applies a different speed cap and a different "
        "tolerance for planner output. Hysteresis prevents mode chattering "
        "near boundaries.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 9, key="c05_seed")
    n = c2.slider("Time steps", 50, 400, 220, 10, key="c05_n")
    static_risk = c3.slider(
        "Inject risk pulse strength", 0.0, 1.0, 0.7, 0.05, key="c05_pulse",
    )
    hyst = c4.slider("Hysteresis", 0.00, 0.20, 0.05, 0.01, key="c05_h")

    rng = np.random.default_rng(seed)
    t = np.arange(n)
    # Synthetic risk signal: baseline + slow wave + pulses + noise
    risk = (
        0.25
        + 0.20 * np.sin(2 * np.pi * t / 80.0)
        + static_risk * np.exp(-((t - n * 0.35) ** 2) / (2 * 18 ** 2))
        + static_risk * 0.7 * np.exp(-((t - n * 0.7) ** 2) / (2 * 12 ** 2))
        + 0.03 * rng.standard_normal(n)
    )
    risk = np.clip(risk, 0.0, 1.0)

    modes, speeds, colors = [], [], []
    prev = "NOMINAL"
    for r in risk:
        m, s, c = _mode_for(float(r), hyst, prev)
        modes.append(m)
        speeds.append(s)
        colors.append(c)
        prev = m

    df = pd.DataFrame({"t": t, "risk": risk, "mode": modes, "speed_scale": speeds})
    transitions = int(df["mode"].ne(df["mode"].shift()).sum() - 1)

    section_header("Risk signal, mode regions and commanded speed")
    fig = go.Figure()
    # Mode bands as shaded background
    for name, lo, hi, _scale, color in MODES:
        fig.add_hrect(y0=lo, y1=min(hi, 1.0), fillcolor=color, opacity=0.12,
                       layer="below", line_width=0)
    fig.add_trace(go.Scatter(
        x=t, y=risk, mode="lines", name="Risk",
        line=dict(color=COLORS["accent"], width=2.0),
    ))
    fig.add_trace(go.Scatter(
        x=t, y=speeds, mode="lines", name="Speed scale",
        line=dict(color=COLORS["primary"], width=2.0, dash="dot"),
        yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title="Risk", range=[0, 1.05]),
        yaxis2=dict(title="Speed scale", overlaying="y", side="right",
                    range=[0, 1.05], color=COLORS["primary"]),
    )
    fig.update_xaxes(title="Time step")
    st.plotly_chart(apply_theme(fig, height=380), use_container_width=True)

    # Mode strip
    section_header("Active-mode timeline")
    fig2 = go.Figure()
    for name, _lo, _hi, _scale, color in MODES:
        mask = df["mode"] == name
        if not mask.any():
            continue
        fig2.add_trace(go.Bar(
            x=df.loc[mask, "t"], y=[1] * int(mask.sum()),
            marker_color=color, name=name, hovertemplate=f"{name}<extra></extra>",
            opacity=0.95, width=1.0,
        ))
    fig2.update_layout(barmode="overlay", bargap=0)
    fig2.update_yaxes(visible=False, range=[0, 1])
    fig2.update_xaxes(title="Time step")
    st.plotly_chart(apply_theme(fig2, height=120), use_container_width=True)

    # Metrics
    fracs = {name: float((df["mode"] == name).mean()) for name, *_ in MODES}
    metrics_row([
        ("Mode transitions", f"{transitions}", COLORS["primary"]),
        ("Avg speed scale", f"{df['speed_scale'].mean():.2f}", COLORS["primary"]),
        ("% time NOMINAL", f"{fracs['NOMINAL']*100:.0f}%", COLORS["success"]),
        ("% time DEGRADED+", f"{(fracs['DEGRADED']+fracs['EMERGENCY'])*100:.0f}%", COLORS["danger"]),
    ])

    interpretation_block(
        f"The FSM triggered <b>{transitions}</b> mode transitions across "
        f"{n} steps. NOMINAL accounts for {fracs['NOMINAL']*100:.0f}% of the "
        f"trace, EMERGENCY for {fracs['EMERGENCY']*100:.0f}%. Increase "
        "hysteresis to smooth out chattering when the risk signal flickers "
        "near a boundary; in practice DynNav tunes this per-mode based on "
        "actuator and planner re-engagement cost."
    )
