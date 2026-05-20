"""C13 — World Model: rollout of predicted future trajectory states."""

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


def _rollout(seed: int, horizon: int, action: float, drift: float, eps_growth: float):
    """Deterministic rollout under a learned-world-model surrogate.

    State: 2D position + velocity. Action is a turn rate. We propagate an
    ensemble of n_samples worlds whose process-noise grows linearly with the
    rollout step — exactly what a learned dynamics model exhibits.
    """
    rng = np.random.default_rng(seed)
    n_samples = 40
    dt = 0.2
    states = np.zeros((n_samples, horizon + 1, 4))  # x, y, vx, vy
    states[:, 0, 2] = 1.0
    states[:, 0, 3] = 0.0

    for t in range(horizon):
        noise = eps_growth * (t + 1) * rng.standard_normal((n_samples, 4))
        vx = states[:, t, 2]
        vy = states[:, t, 3]
        # Apply rotation by `action` per step
        cos_a, sin_a = np.cos(action * dt), np.sin(action * dt)
        new_vx = cos_a * vx - sin_a * vy + drift * dt
        new_vy = sin_a * vx + cos_a * vy
        states[:, t + 1, 0] = states[:, t, 0] + new_vx * dt + 0.02 * noise[:, 0]
        states[:, t + 1, 1] = states[:, t, 1] + new_vy * dt + 0.02 * noise[:, 1]
        states[:, t + 1, 2] = new_vx + 0.03 * noise[:, 2]
        states[:, t + 1, 3] = new_vy + 0.03 * noise[:, 3]
    return states


def render(st_ctx=st) -> None:
    explanation_block(
        "C13 — World Model: Imagined Rollouts under a Learned Dynamics Model",
        "Model-based RL learns a compact dynamics model — a 'world model' — "
        "and uses it to imagine trajectories without interacting with the "
        "real environment. DynNav samples ensembles of rollouts whose "
        "epistemic uncertainty grows with the horizon (modelled here as "
        "linearly-increasing process noise). The planner then evaluates "
        "candidate actions by their imagined-return statistics, picking "
        "actions that are good in expectation and robust across the "
        "ensemble.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 14, key="c13_seed")
    horizon = c2.slider("Rollout horizon (steps)", 10, 80, 40, key="c13_h")
    action = c3.slider("Constant action (turn rate)", -1.0, 1.0, 0.25, 0.05, key="c13_a")
    eps = c4.slider("Epistemic spread", 0.0, 1.0, 0.35, 0.02, key="c13_e")

    states = _rollout(seed, horizon, action, drift=0.1, eps_growth=eps)
    mean_xy = states.mean(axis=0)
    std_xy = states.std(axis=0)

    section_header("Imagined trajectory ensemble")
    fig = go.Figure()
    # Per-sample faint paths
    for k in range(states.shape[0]):
        fig.add_trace(go.Scatter(
            x=states[k, :, 0], y=states[k, :, 1], mode="lines",
            line=dict(color="rgba(34,211,238,0.07)", width=1),
            showlegend=False, hoverinfo="skip",
        ))
    # Mean trajectory
    fig.add_trace(go.Scatter(
        x=mean_xy[:, 0], y=mean_xy[:, 1], mode="lines",
        line=dict(color=COLORS["secondary"], width=3),
        name="Mean trajectory",
    ))
    # Uncertainty hull at end-time
    final_x = states[:, -1, 0]
    final_y = states[:, -1, 1]
    fig.add_trace(go.Scatter(
        x=final_x, y=final_y, mode="markers",
        marker=dict(color=COLORS["highlight"], size=6, opacity=0.85),
        name="Terminal samples",
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=dict(color=COLORS["primary"], size=18, symbol="square",
                    line=dict(color="#0E1117", width=1.5)),
        name="Start",
    ))
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=440), use_container_width=True)

    section_header("Per-step uncertainty (std of x, y)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        y=std_xy[:, 0], mode="lines", name="σ(x)",
        line=dict(color=COLORS["primary"], width=2),
    ))
    fig2.add_trace(go.Scatter(
        y=std_xy[:, 1], mode="lines", name="σ(y)",
        line=dict(color=COLORS["accent"], width=2, dash="dot"),
    ))
    fig2.update_xaxes(title="Step")
    fig2.update_yaxes(title="Standard deviation")
    st.plotly_chart(apply_theme(fig2, height=240), use_container_width=True)

    metrics_row([
        ("Final mean x", f"{mean_xy[-1, 0]:+.2f}", COLORS["secondary"]),
        ("Final mean y", f"{mean_xy[-1, 1]:+.2f}", COLORS["secondary"]),
        ("Final σ(x)", f"{std_xy[-1, 0]:.3f}", COLORS["accent"]),
        ("Final σ(y)", f"{std_xy[-1, 1]:.3f}", COLORS["accent"]),
        ("Horizon", f"{horizon} steps", COLORS["primary"]),
    ])

    interpretation_block(
        f"After {horizon} imagined steps, the ensemble's terminal "
        f"uncertainty is σ ≈ ({std_xy[-1, 0]:.2f}, {std_xy[-1, 1]:.2f}). "
        "DynNav's planner penalises actions whose imagined return has "
        "high variance — a model-based analogue of risk aversion. With "
        "epistemic spread set to 0, the rollouts collapse onto a single "
        "deterministic trajectory; with spread large, the planner becomes "
        "cautious and shortens its effective horizon."
    )
