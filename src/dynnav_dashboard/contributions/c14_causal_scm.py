"""C14 — Causal SCM: counterfactual failure explanation."""

from __future__ import annotations

import numpy as np
import networkx as nx
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


# Synthetic SCM for a navigation failure:
#   Fog -> SensorNoise -> EstimatorError -> PlannerRisk -> Collision
#   Speed -> ReactionTime -> Collision
#   Battery -> ReplanRate  -> PlannerRisk
NODES = [
    "Fog",            # exogenous
    "Speed",          # exogenous (commanded)
    "Battery",        # exogenous
    "SensorNoise",
    "EstimatorError",
    "ReactionTime",
    "ReplanRate",
    "PlannerRisk",
    "Collision",
]

EDGES = [
    ("Fog", "SensorNoise"),
    ("SensorNoise", "EstimatorError"),
    ("EstimatorError", "PlannerRisk"),
    ("PlannerRisk", "Collision"),
    ("Speed", "ReactionTime"),
    ("ReactionTime", "Collision"),
    ("Battery", "ReplanRate"),
    ("ReplanRate", "PlannerRisk"),
]


def _evaluate(fog, speed, battery):
    """Forward-evaluate the SCM. Higher = worse for each downstream."""
    sensor_noise = 0.1 + 0.7 * fog
    estimator_err = sensor_noise * (0.4 + 0.6 * fog) + 0.05
    reaction = 0.1 + 0.8 * speed
    replan = max(0.05, 0.5 - 0.4 * battery)  # low battery -> slow replan
    planner_risk = 0.5 * estimator_err + 0.4 * replan
    collision = float(np.clip(0.5 * planner_risk + 0.5 * reaction + 0.02, 0, 1))
    return {
        "Fog": fog, "Speed": speed, "Battery": battery,
        "SensorNoise": sensor_noise, "EstimatorError": estimator_err,
        "ReactionTime": reaction, "ReplanRate": replan,
        "PlannerRisk": planner_risk, "Collision": collision,
    }


def _counterfactuals(observed):
    """Run a counterfactual per exogenous variable: 'what if it were nominal?'"""
    nominal = {"Fog": 0.1, "Speed": 0.3, "Battery": 0.8}
    cfs = {}
    for k, v in nominal.items():
        cf = dict(observed)
        cf[k] = v
        result = _evaluate(cf["Fog"], cf["Speed"], cf["Battery"])
        cfs[k] = result
    return cfs


def render(st_ctx=st) -> None:
    explanation_block(
        "C14 — Causal SCM: Counterfactual Failure Explanation",
        "A Structural Causal Model (SCM) encodes the causal pathways "
        "through which exogenous factors (fog, speed, battery) propagate "
        "to a failure (collision). After an incident, DynNav runs a "
        "counterfactual analysis: <i>what if</i> fog had been nominal? "
        "<i>what if</i> the commanded speed had been lower? The largest "
        "drop in failure probability identifies the single most causally "
        "responsible factor — a defensible explanation, not just a "
        "correlation.",
    )

    section_header("Interactive controls — observed conditions during incident")
    c1, c2, c3 = st.columns(3)
    fog = c1.slider("Fog level", 0.0, 1.0, 0.85, 0.05, key="c14_fog")
    speed = c2.slider("Commanded speed", 0.0, 1.0, 0.75, 0.05, key="c14_sp")
    battery = c3.slider("Battery level", 0.0, 1.0, 0.25, 0.05, key="c14_b")

    observed = _evaluate(fog, speed, battery)
    cfs = _counterfactuals(observed)

    # Causal graph
    section_header("Causal graph (red node = collision; colour = magnitude)")
    G = nx.DiGraph()
    for n in NODES:
        G.add_node(n)
    for u, v in EDGES:
        G.add_edge(u, v)
    pos = {
        "Fog": (0, 2), "Speed": (0, 1), "Battery": (0, 0),
        "SensorNoise": (1, 2),
        "EstimatorError": (2, 2),
        "ReactionTime": (1.5, 1),
        "ReplanRate": (1.5, 0),
        "PlannerRisk": (3, 1.2),
        "Collision": (4, 1),
    }

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="rgba(110,118,129,0.55)", width=1.5),
        hoverinfo="none", showlegend=False,
    ))
    # Arrowheads
    for u, v in G.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        fig.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2,
            arrowcolor="rgba(110,118,129,0.65)", arrowwidth=1.3,
        )
    nx_x = [pos[n][0] for n in NODES]
    nx_y = [pos[n][1] for n in NODES]
    node_vals = [observed[n] for n in NODES]
    node_colors = [
        COLORS["danger"] if n == "Collision" else COLORS["secondary"]
        for n in NODES
    ]
    fig.add_trace(go.Scatter(
        x=nx_x, y=nx_y, mode="markers+text",
        marker=dict(
            color=node_colors, size=42,
            line=dict(color="#0E1117", width=2.0),
            opacity=[0.55 + 0.45 * float(v) for v in node_vals],
        ),
        text=[f"{n}<br>{observed[n]:.2f}" for n in NODES],
        textposition="middle center",
        textfont=dict(size=10, color=COLORS["text"]),
        hoverinfo="text", showlegend=False,
    ))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    st.plotly_chart(apply_theme(fig, height=420), use_container_width=True)

    # Counterfactual ranking
    section_header("Counterfactual analysis — change vs observed collision probability")
    base = observed["Collision"]
    rows = []
    for k, v in cfs.items():
        delta = base - v["Collision"]
        rows.append({"Intervention": f"set {k} to nominal", "Δ collision": delta,
                      "Counterfactual P(coll.)": v["Collision"]})
    rows.sort(key=lambda r: r["Δ collision"], reverse=True)

    labels = [r["Intervention"] for r in rows]
    deltas = [r["Δ collision"] for r in rows]
    fig2 = go.Figure(go.Bar(
        x=deltas, y=labels, orientation="h",
        marker_color=[
            COLORS["success"] if d > 0 else COLORS["text_muted"] for d in deltas
        ],
        text=[f"Δ = -{d:.3f}" for d in deltas], textposition="auto",
    ))
    fig2.update_xaxes(title="Reduction in collision probability")
    st.plotly_chart(apply_theme(fig2, height=240), use_container_width=True)

    metrics_row([
        ("Observed P(collision)", f"{base:.3f}", COLORS["danger"]),
        ("Top causal factor", rows[0]["Intervention"], COLORS["highlight"]),
        ("Best Δ", f"-{rows[0]['Δ collision']:.3f}", COLORS["success"]),
    ])

    interpretation_block(
        f"Holding everything else fixed, intervening on <b>"
        f"{rows[0]['Intervention'].replace('set ', '').replace(' to nominal', '')}"
        f"</b> would reduce the predicted collision probability the most "
        f"(by {rows[0]['Δ collision']:.3f}). Note how reducing fog can "
        "matter more than reducing speed when sensor noise is the dominant "
        "pathway — a finding a correlation-only diagnostic would miss."
    )
