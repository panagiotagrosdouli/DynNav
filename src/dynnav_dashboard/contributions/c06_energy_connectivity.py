"""C06 — Energy & Connectivity: feasibility under battery and link constraints."""

from __future__ import annotations

import math

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
    square_axes,
)


def _waypoint_chain(seed: int, base_station: tuple[float, float], scale: float = 10.0):
    rng = np.random.default_rng(seed)
    pts = [(base_station[0] + 1.5, base_station[1] + 1.0)]
    for _ in range(8):
        last = pts[-1]
        pts.append((last[0] + rng.uniform(1.0, 3.0), last[1] + rng.uniform(-1.0, 2.5)))
    return pts


def render(st_ctx=st) -> None:
    explanation_block(
        "C06 — Energy & Connectivity Constraints",
        "Two hard constraints quietly dominate field robotics: battery and "
        "radio link. A path that is geometrically optimal may exceed the "
        "robot's energy budget, or drag it out of a comms tether to a "
        "ground station. DynNav models both: each edge has an energy cost "
        "and the planner rejects any waypoint whose Euclidean distance to "
        "the base exceeds the link budget. The result is a feasible — not "
        "just shortest — plan.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 11, key="c06_seed")
    battery = c2.slider("Battery (Wh)", 5.0, 60.0, 25.0, 1.0, key="c06_b")
    link_radius = c3.slider("Comms link radius (m)", 4.0, 25.0, 12.0, 0.5, key="c06_l")
    cost_per_m = c4.slider("Energy cost (Wh/m)", 0.05, 1.50, 0.45, 0.05, key="c06_e")

    base = (1.5, 1.5)
    waypoints = _waypoint_chain(seed, base)

    # Greedy / cumulative feasibility check
    cum_energy = 0.0
    feasible_idx = 0
    infeasible_reason = None
    last = (base[0], base[1])
    for i, p in enumerate(waypoints):
        leg = math.hypot(p[0] - last[0], p[1] - last[1])
        e = leg * cost_per_m
        # Check link
        link = math.hypot(p[0] - base[0], p[1] - base[1])
        if link > link_radius:
            infeasible_reason = f"link broken at WP{i+1} ({link:.1f} m > {link_radius:.1f} m)"
            break
        if cum_energy + e > battery:
            infeasible_reason = (
                f"battery exhausted at WP{i+1} "
                f"({cum_energy + e:.1f} Wh > {battery:.1f} Wh)"
            )
            break
        cum_energy += e
        feasible_idx = i + 1
        last = p
    success = infeasible_reason is None

    # Plot
    section_header("Mission map (base = blue square, link disc shaded)")
    fig = go.Figure()
    # Link disc
    theta = np.linspace(0, 2 * np.pi, 80)
    fig.add_trace(go.Scatter(
        x=base[0] + link_radius * np.cos(theta),
        y=base[1] + link_radius * np.sin(theta),
        fill="toself", mode="lines",
        line=dict(color=COLORS["secondary"], width=1, dash="dot"),
        fillcolor="rgba(34,211,238,0.08)", name="Link coverage",
        hoverinfo="skip",
    ))
    # Base
    fig.add_trace(go.Scatter(
        x=[base[0]], y=[base[1]], mode="markers+text",
        marker=dict(color=COLORS["primary"], size=18, symbol="square",
                    line=dict(color="#0E1117", width=2)),
        text=["Base"], textposition="top center",
        name="Base station",
    ))
    # Waypoints
    wx = [p[0] for p in waypoints]
    wy = [p[1] for p in waypoints]
    colors_pts = [
        COLORS["success"] if i < feasible_idx else COLORS["danger"]
        for i in range(len(waypoints))
    ]
    fig.add_trace(go.Scatter(
        x=wx, y=wy, mode="markers+text",
        marker=dict(color=colors_pts, size=12,
                    line=dict(color="#0E1117", width=1.5)),
        text=[f"WP{i+1}" for i in range(len(waypoints))],
        textposition="bottom center",
        textfont=dict(color="rgba(230,237,243,0.85)"),
        name="Waypoints", hoverinfo="text",
    ))
    # Feasible polyline
    if feasible_idx >= 1:
        fxs = [base[0]] + wx[:feasible_idx]
        fys = [base[1]] + wy[:feasible_idx]
        fig.add_trace(go.Scatter(
            x=fxs, y=fys, mode="lines", name="Feasible segment",
            line=dict(color=COLORS["success"], width=3),
        ))
    # Infeasible tail
    if feasible_idx < len(waypoints):
        ixs = wx[max(feasible_idx - 1, 0):]
        iys = wy[max(feasible_idx - 1, 0):]
        # connect from last feasible point (or base) to the infeasible portion
        if feasible_idx == 0:
            ixs = [base[0]] + wx
            iys = [base[1]] + wy
        fig.add_trace(go.Scatter(
            x=ixs, y=iys, mode="lines", name="Infeasible segment",
            line=dict(color=COLORS["danger"], width=2, dash="dot"),
        ))
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=440), use_container_width=True)

    metrics_row([
        ("Reached waypoints", f"{feasible_idx} / {len(waypoints)}",
         COLORS["success"] if success else COLORS["danger"]),
        ("Energy used", f"{cum_energy:.2f} / {battery:.1f} Wh", COLORS["primary"]),
        ("Battery margin", f"{max(battery - cum_energy, 0):.2f} Wh", COLORS["success"]),
        ("Mission status", "FEASIBLE" if success else "INFEASIBLE",
         COLORS["success"] if success else COLORS["danger"]),
    ])

    if not success:
        st.warning(f"Constraint violation: {infeasible_reason}")

    interpretation_block(
        "Battery and link budgets are coupled: a wider comms ring may let "
        "the robot reach a distant waypoint but at the cost of energy spent "
        "traversing the distance. Try shrinking the link radius — at some "
        "point the closest waypoints stay feasible while the chain breaks "
        "halfway through. DynNav surfaces both numbers so a supervisor can "
        "see why the mission was clipped."
    )
