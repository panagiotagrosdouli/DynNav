"""C18 — CBF / STL Safety Shields: filter unsafe controls to safe ones."""

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


def _shield_control(
    pos, vel, u_nom, obstacles, alpha: float, dt: float, safety_radius: float,
):
    """Apply a 2-D Control Barrier Function safety shield.

    For each obstacle define h(x) = ||x - x_obs||^2 - r^2. The CBF condition
    requires h_dot + alpha * h >= 0, equivalently:

        2 * (x - x_obs) · u + 2 * (x - x_obs) · vel + alpha * h >= 0

    We solve a tiny QP-by-projection: project u_nom onto the half-space that
    satisfies the most-binding constraint, and iterate.
    """
    u = np.array(u_nom, dtype=float)
    pos = np.asarray(pos, dtype=float)
    vel = np.asarray(vel, dtype=float)
    for _ in range(8):
        violated = False
        for ox, oy in obstacles:
            delta = pos - np.array([ox, oy])
            h = float(delta @ delta - safety_radius ** 2)
            # ∇h · (vel + u) + alpha * h >= 0
            g = 2.0 * delta
            lhs = float(g @ (vel + u) + alpha * h)
            if lhs < 0.0:
                # Project u to satisfy lhs = 0
                # ∇h · u + (∇h · vel + alpha h) = 0
                k = float(g @ g)
                if k < 1e-9:
                    continue
                u = u - (lhs / k) * g
                violated = True
        if not violated:
            break
    return u


def render(st_ctx=st) -> None:
    explanation_block(
        "C18 — CBF / STL Safety Shields",
        "A safety shield is a thin filter sitting between an upstream "
        "controller (PID, MPC, or RL policy) and the actuators. The shield "
        "checks every commanded action against a formal safety constraint — "
        "Control Barrier Functions (CBFs) for forward invariance of a safe "
        "set, Signal Temporal Logic (STL) for time-bounded specifications — "
        "and minimally modifies the command if it would violate the spec. "
        "DynNav uses CBFs to guarantee distance to obstacles regardless of "
        "what the learned policy proposes.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 3, key="c18_seed")
    horizon = c2.slider("Horizon (steps)", 30, 200, 100, 10, key="c18_h")
    alpha = c3.slider("CBF α (assertiveness)", 0.5, 8.0, 3.0, 0.1, key="c18_a")
    radius = c4.slider("Safety radius", 0.5, 3.0, 1.2, 0.1, key="c18_r")

    rng = np.random.default_rng(seed)
    obstacles = [(3.0, 2.0), (5.5, 3.5), (6.5, 1.5)]
    dt = 0.1
    pos_nom = np.array([0.0, 2.0]); vel_nom = np.array([0.0, 0.0])
    pos_shield = pos_nom.copy(); vel_shield = vel_nom.copy()

    # Nominal controller: PID-like attraction to a goal that drives the robot
    # straight through the obstacle row.
    goal = np.array([8.0, 2.0])
    traj_nom, traj_shield, u_nom_hist, u_safe_hist = [], [], [], []

    interventions = 0
    nominal_collisions = 0
    shield_collisions = 0

    for step in range(horizon):
        traj_nom.append(pos_nom.copy())
        traj_shield.append(pos_shield.copy())

        u_nom_n = 1.5 * (goal - pos_nom) - 0.4 * vel_nom
        u_nom_s = 1.5 * (goal - pos_shield) - 0.4 * vel_shield
        u_safe = _shield_control(
            pos_shield, vel_shield, u_nom_s, obstacles,
            alpha=alpha, dt=dt, safety_radius=radius,
        )
        if not np.allclose(u_safe, u_nom_s, atol=1e-3):
            interventions += 1

        u_nom_hist.append(float(np.linalg.norm(u_nom_n)))
        u_safe_hist.append(float(np.linalg.norm(u_safe)))

        # Step nominal (no shield)
        vel_nom = vel_nom + u_nom_n * dt
        vel_nom = np.clip(vel_nom, -2.5, 2.5)
        pos_nom = pos_nom + vel_nom * dt
        # Step shielded
        vel_shield = vel_shield + u_safe * dt
        vel_shield = np.clip(vel_shield, -2.5, 2.5)
        pos_shield = pos_shield + vel_shield * dt

        for ox, oy in obstacles:
            if (pos_nom[0] - ox) ** 2 + (pos_nom[1] - oy) ** 2 < radius ** 2:
                nominal_collisions += 1
                break
        for ox, oy in obstacles:
            if (pos_shield[0] - ox) ** 2 + (pos_shield[1] - oy) ** 2 < radius ** 2:
                shield_collisions += 1
                break

    traj_nom = np.array(traj_nom); traj_shield = np.array(traj_shield)

    section_header("Trajectories: nominal vs shielded")
    fig = go.Figure()
    # Safe rings
    theta = np.linspace(0, 2 * np.pi, 80)
    for i, (ox, oy) in enumerate(obstacles):
        fig.add_trace(go.Scatter(
            x=ox + radius * np.cos(theta), y=oy + radius * np.sin(theta),
            fill="toself", mode="lines",
            line=dict(color=COLORS["danger"], width=1, dash="dot"),
            fillcolor="rgba(239,68,68,0.10)",
            name="Safety ring" if i == 0 else None, showlegend=(i == 0),
            hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter(
        x=traj_nom[:, 0], y=traj_nom[:, 1], mode="lines",
        name="Nominal (unshielded)",
        line=dict(color=COLORS["danger"], width=2, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=traj_shield[:, 0], y=traj_shield[:, 1], mode="lines",
        name="CBF-shielded",
        line=dict(color=COLORS["secondary"], width=3),
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=[2], mode="markers", name="Start",
        marker=dict(color=COLORS["primary"], size=14, symbol="square",
                     line=dict(color="#0E1117", width=1.5)),
    ))
    fig.add_trace(go.Scatter(
        x=[goal[0]], y=[goal[1]], mode="markers", name="Goal",
        marker=dict(color=COLORS["success"], size=16, symbol="star",
                     line=dict(color="#0E1117", width=1.5)),
    ))
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=400), use_container_width=True)

    section_header("Nominal vs filtered control magnitudes")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=u_nom_hist, name="‖u_nominal‖", mode="lines",
                                line=dict(color=COLORS["danger"], width=2)))
    fig2.add_trace(go.Scatter(y=u_safe_hist, name="‖u_safe‖", mode="lines",
                                line=dict(color=COLORS["secondary"], width=2, dash="dot")))
    fig2.update_xaxes(title="Step")
    fig2.update_yaxes(title="Control magnitude")
    st.plotly_chart(apply_theme(fig2, height=220), use_container_width=True)

    metrics_row([
        ("Shield interventions", f"{interventions} / {horizon}", COLORS["highlight"]),
        ("Nominal collisions", f"{nominal_collisions}", COLORS["danger"]),
        ("Shielded collisions", f"{shield_collisions}",
         COLORS["success"] if shield_collisions == 0 else COLORS["danger"]),
        ("Intervention rate",
         f"{interventions / max(horizon, 1) * 100:.0f}%", COLORS["primary"]),
    ])

    interpretation_block(
        f"The CBF shield intervened on {interventions} of {horizon} steps. "
        f"The unshielded controller registered {nominal_collisions} "
        f"collisions; the shielded version registered {shield_collisions}. "
        "The shield never tries to outperform the upstream policy on "
        "performance — it only minimally edits commands that would breach "
        "the safe set. Increase α to make the filter more aggressive earlier "
        "(robot turns away sooner); decrease α for last-moment corrections."
    )
