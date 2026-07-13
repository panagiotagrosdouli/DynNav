from __future__ import annotations

from dataclasses import replace

import matplotlib.pyplot as plt
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.simulation import build_environment, plan_astar, plan_risk_aware

st.set_page_config(page_title="DynNav Research Dashboard", page_icon="🧭", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 2rem;}
    .status-card {border: 1px solid #334155; border-radius: 14px; padding: 1rem; background: #0f172a;}
    .small-note {color: #94a3b8; font-size: .9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("DynNav")
st.caption("Deterministic explanatory dashboard for uncertainty-aware and risk-aware navigation research.")
st.info(
    "Synthetic validation only. This dashboard does not claim ROS 2, hardware, field, or certified-safety validation."
)

with st.sidebar:
    st.header("Scenario")
    seed = st.number_input("Seed", min_value=0, max_value=100_000, value=7, step=1)
    risk_weight = st.slider("Risk weight", min_value=0.0, max_value=6.0, value=2.5, step=0.1)
    show_uncertainty = st.checkbox("Show uncertainty", value=True)
    show_risk = st.checkbox("Show risk", value=True)
    st.caption("Changing the seed regenerates the same scenario deterministically.")

cfg = replace(DEFAULT_SCENARIO, random_seed=int(seed), risk_weight=float(risk_weight))
env = build_environment(cfg, seed=int(seed))
shortest = plan_astar(env, cfg.start, cfg.goal)
risk_aware = plan_risk_aware(env, cfg.start, cfg.goal, cfg.risk_weight)

shortest_path = list(getattr(shortest, "path", []))
risk_path = list(getattr(risk_aware, "path", []))

m1, m2, m3, m4 = st.columns(4)
m1.metric("Grid", f"{cfg.grid_size} × {cfg.grid_size}")
m2.metric("Shortest-path cells", len(shortest_path))
m3.metric("DynNav-path cells", len(risk_path))
m4.metric("Risk weight", f"{cfg.risk_weight:.1f}")

fig, ax = plt.subplots(figsize=(9, 7))
ax.imshow(env.occupancy, origin="lower", cmap="Greys", alpha=0.8)
if show_uncertainty:
    ax.imshow(env.uncertainty, origin="lower", cmap="Purples", alpha=0.28)
if show_risk:
    ax.imshow(env.risk, origin="lower", cmap="Oranges", alpha=0.25)
if shortest_path:
    sx, sy = zip(*shortest_path)
    ax.plot(sx, sy, linestyle="--", linewidth=1.8, label="Shortest route")
if risk_path:
    rx, ry = zip(*risk_path)
    ax.plot(rx, ry, linewidth=2.8, label="DynNav risk-aware route")
ax.scatter(*cfg.start, marker="o", s=90, label="Start")
ax.scatter(*cfg.goal, marker="*", s=150, label="Goal")
ax.set_title("Synthetic occupancy belief, uncertainty, risk, and candidate routes")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.legend(loc="upper left")
ax.set_aspect("equal")
st.pyplot(fig, clear_figure=True)

left, right = st.columns(2)
with left:
    st.subheader("What this app demonstrates")
    st.markdown(
        """
        - deterministic synthetic scenario generation;
        - occupancy, uncertainty, and risk layers;
        - shortest-path and risk-aware route comparison;
        - transparent controls without hidden benchmark claims.
        """
    )
with right:
    st.subheader("Current research status")
    st.markdown(
        """
        **Implemented prototype:** deterministic grid planning and visual comparison.  
        **Simulation validation pending:** ROS 2/Nav2 and Gazebo integration.  
        **Hardware validation required:** no physical-robot safety claim is made.
        """
    )

st.divider()
st.markdown(
    '<p class="small-note">Run with <code>python -m pip install -e ".[dashboard]"</code> and '
    '<code>streamlit run app/dashboard.py</code>.</p>',
    unsafe_allow_html=True,
)
