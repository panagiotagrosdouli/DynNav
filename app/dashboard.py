from __future__ import annotations

from dataclasses import replace

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.simulation import (
    build_environment,
    plan_astar,
    plan_risk_aware,
    simulate_rollout,
)

st.set_page_config(page_title="DynNav Research Dashboard", page_icon="🧭", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1320px; padding-top: 1.5rem;}
    .small-note {color: #64748b; font-size: .9rem;}
    .decision-card {
        border: 1px solid #cbd5e1;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        background: rgba(148, 163, 184, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧭 DynNav — Inside the Navigation Loop")
st.caption(
    "Interactive, deterministic visualization of occupancy, uncertainty, risk-aware planning, "
    "dynamic-obstacle monitoring, online replanning, and mission supervision."
)
st.info(
    "Synthetic research visualization only. It is not ROS 2 execution, hardware evidence, "
    "a collision-probability guarantee, or a certified safety controller."
)

with st.sidebar:
    st.header("Scenario controls")
    seed = st.number_input("Random seed", min_value=0, max_value=100_000, value=7, step=1)
    risk_weight = st.slider("Risk weight", 0.0, 6.0, 2.5, 0.1)
    planner_mode = st.radio("Closed-loop planner", ["Risk-aware A*", "Classical A*"], index=0)
    dynamic_step_every = st.slider("Move dynamic obstacles every N steps", 1, 6, 2)
    show_uncertainty = st.checkbox("Overlay uncertainty", value=True)
    show_risk = st.checkbox("Overlay risk", value=True)
    show_baseline = st.checkbox("Show initial A* baseline", value=True)
    st.caption("The same seed always regenerates the same synthetic scenario.")

cfg = replace(DEFAULT_SCENARIO, random_seed=int(seed), risk_weight=float(risk_weight))
env = build_environment(cfg, seed=int(seed))
baseline = plan_astar(env, cfg.start, cfg.goal)
risk_plan = plan_risk_aware(env, cfg.start, cfg.goal, cfg.risk_weight)
rollout = simulate_rollout(
    env,
    cfg,
    use_risk_aware=planner_mode == "Risk-aware A*",
    dynamic_step_every=int(dynamic_step_every),
)

if not rollout.frames:
    st.error("The simulation produced no frames for this scenario.")
    st.stop()

if "frame_index" not in st.session_state:
    st.session_state.frame_index = 0
st.session_state.frame_index = min(st.session_state.frame_index, len(rollout.frames) - 1)

nav_left, nav_mid, nav_right = st.columns([1, 4, 1])
with nav_left:
    if st.button("◀ Previous", use_container_width=True):
        st.session_state.frame_index = max(0, st.session_state.frame_index - 1)
with nav_mid:
    frame_index = st.slider(
        "Simulation step",
        min_value=0,
        max_value=len(rollout.frames) - 1,
        value=st.session_state.frame_index,
        key="frame_slider",
    )
    st.session_state.frame_index = frame_index
with nav_right:
    if st.button("Next ▶", use_container_width=True):
        st.session_state.frame_index = min(len(rollout.frames) - 1, st.session_state.frame_index + 1)
        st.rerun()

frame = rollout.frames[st.session_state.frame_index]
robot_x, robot_y = frame.robot
local_risk = float(frame.risk_snapshot[robot_y, robot_x])
local_uncertainty = float(env.uncertainty[robot_y, robot_x])

if rollout.reached_goal and frame.step == rollout.frames[-1].step:
    supervisor_state = "GOAL REACHED"
elif not frame.path_remaining:
    supervisor_state = "SAFE STOP"
elif frame.replanned:
    supervisor_state = "REPLAN"
elif local_risk >= 0.70 or local_uncertainty >= 0.75:
    supervisor_state = "CAUTION"
else:
    supervisor_state = "NORMAL"

metric_cols = st.columns(6)
metric_cols[0].metric("Step", frame.step)
metric_cols[1].metric("Supervisor", supervisor_state)
metric_cols[2].metric("Replans", frame.replan_count)
metric_cols[3].metric("Local risk", f"{local_risk:.3f}")
metric_cols[4].metric("Local uncertainty", f"{local_uncertainty:.3f}")
metric_cols[5].metric("Remaining cells", len(frame.path_remaining))

map_tab, pipeline_tab, metrics_tab, evidence_tab = st.tabs(
    ["Live navigation", "Inside the pipeline", "Planner metrics", "Evidence boundary"]
)

with map_tab:
    plot_col, explanation_col = st.columns([2.2, 1])

    with plot_col:
        fig, ax = plt.subplots(figsize=(9.5, 7.5))
        occupancy = np.clip(env.static + frame.dynamic_snapshot, 0, 1)
        ax.imshow(occupancy, origin="lower", cmap="Greys", alpha=0.90)
        if show_uncertainty:
            ax.imshow(env.uncertainty, origin="lower", cmap="Purples", alpha=0.25)
        if show_risk:
            ax.imshow(frame.risk_snapshot, origin="lower", cmap="Oranges", alpha=0.28)

        if show_baseline and baseline.path:
            bx, by = zip(*baseline.path)
            ax.plot(bx, by, "--", linewidth=1.5, label="Initial shortest-path A*")

        if frame.path_remaining:
            px, py = zip(*frame.path_remaining)
            ax.plot(px, py, linewidth=2.8, label="Current active route")

        dyn_y, dyn_x = np.where(frame.dynamic_snapshot > 0.5)
        if len(dyn_x):
            ax.scatter(dyn_x, dyn_y, marker="s", s=38, label="Dynamic obstacle")

        ax.scatter(robot_x, robot_y, marker="o", s=130, label="Robot")
        ax.scatter(*cfg.start, marker="o", s=70, facecolors="none", label="Start")
        ax.scatter(*cfg.goal, marker="*", s=180, label="Goal")
        ax.set_title(f"Closed-loop navigation — step {frame.step}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_aspect("equal")
        ax.legend(loc="upper left", fontsize=8)
        st.pyplot(fig, clear_figure=True)

    with explanation_col:
        st.subheader("Why this state?")
        if supervisor_state == "REPLAN":
            explanation = (
                "The route monitor detected that the current path was blocked or compromised. "
                "The planner recomputed a route from the robot's current position."
            )
        elif supervisor_state == "CAUTION":
            explanation = (
                "The robot is still moving, but the local risk or uncertainty field is elevated. "
                "A mission supervisor would reduce trust in the nominal route and monitor more closely."
            )
        elif supervisor_state == "SAFE STOP":
            explanation = (
                "No usable route is currently available. The explanatory supervisor chooses a safe-stop state "
                "instead of inventing a path through occupied space."
            )
        elif supervisor_state == "GOAL REACHED":
            explanation = "The robot reached the goal and the navigation episode terminates successfully."
        else:
            explanation = (
                "The active route remains traversable and local risk is below the explanatory caution threshold. "
                "The robot continues along the current plan."
            )

        st.markdown(f'<div class="decision-card"><strong>{supervisor_state}</strong><br><br>{explanation}</div>', unsafe_allow_html=True)
        st.markdown("### Current signals")
        st.progress(min(max(local_risk, 0.0), 1.0), text=f"Risk: {local_risk:.3f}")
        st.progress(min(max(local_uncertainty, 0.0), 1.0), text=f"Uncertainty: {local_uncertainty:.3f}")
        st.write(f"Robot cell: `{frame.robot}`")
        st.write(f"Planning runtime this step: `{frame.runtime_ms:.3f} ms`")
        st.write(f"Replanned now: `{'yes' if frame.replanned else 'no'}`")

with pipeline_tab:
    st.subheader("What happens inside DynNav")
    stages = [
        ("1. Observe", "Read the current occupancy and dynamic-obstacle state."),
        ("2. Estimate", "Construct uncertainty and spatial risk fields."),
        ("3. Plan", "Compare geometric travel cost with the configured risk penalty."),
        ("4. Monitor", "Check whether the forward path becomes occupied or undesirable."),
        ("5. Decide", "Continue, enter caution, replan, stop safely, or finish at the goal."),
        ("6. Record", "Preserve route, risk, runtime, replans, and outcome for audit."),
    ]
    for title, description in stages:
        st.markdown(f"**{title}** — {description}")

    st.code(
        "observe → update belief → estimate uncertainty/risk → plan → monitor → "
        "continue/replan/stop → record evidence",
        language="text",
    )
    st.caption(
        "The dashboard uses a lightweight synthetic engine. It mirrors the intended decision structure, "
        "but it does not claim that every repository contribution is executing in this single app."
    )

with metrics_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Initial candidate comparison")
        st.dataframe(
            {
                "metric": ["success", "path cells", "expansions", "runtime ms", "cost", "average risk", "maximum risk"],
                "A* baseline": [
                    baseline.success,
                    len(baseline.path),
                    baseline.expansions,
                    round(baseline.runtime_ms, 3),
                    round(baseline.cost, 3),
                    round(baseline.avg_risk, 3),
                    round(baseline.max_risk, 3),
                ],
                "Risk-aware A*": [
                    risk_plan.success,
                    len(risk_plan.path),
                    risk_plan.expansions,
                    round(risk_plan.runtime_ms, 3),
                    round(risk_plan.cost, 3),
                    round(risk_plan.avg_risk, 3),
                    round(risk_plan.max_risk, 3),
                ],
            },
            use_container_width=True,
            hide_index=True,
        )
    with right:
        st.subheader("Closed-loop episode")
        episode_metrics = {
            "Reached goal": rollout.reached_goal,
            "Final robot cell": rollout.final_robot,
            "Executed distance": round(rollout.total_distance, 3),
            "Total replans": rollout.total_replans,
            "Average risk": round(rollout.avg_risk, 3),
            "Maximum risk": round(rollout.max_risk, 3),
            "Average planning time (ms)": round(rollout.avg_compute_ms, 3),
            "Blocked dynamic steps": rollout.collisions,
        }
        st.json(episode_metrics)

with evidence_tab:
    st.subheader("How to interpret this dashboard")
    st.markdown(
        """
        **Demonstrated here**
        - deterministic synthetic environment generation;
        - static and moving obstacles;
        - uncertainty and obstacle-proximity risk fields;
        - classical and risk-aware A* comparison;
        - online path invalidation and replanning;
        - transparent, explanatory supervisor states;
        - episode-level metrics.

        **Not demonstrated here**
        - ROS 2 or Nav2 execution;
        - Gazebo or physical-robot validation;
        - calibrated collision probabilities;
        - formal recoverability or safety guarantees;
        - production deployment readiness.
        """
    )

st.divider()
st.markdown(
    '<p class="small-note">Install with <code>python -m pip install -e ".[dashboard]"</code> and run '
    '<code>streamlit run app/dashboard.py</code>.</p>',
    unsafe_allow_html=True,
)
