from __future__ import annotations

from dataclasses import replace

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.contributions import RENDERERS
from dynnav_dashboard.simulation import (
    build_environment,
    plan_astar,
    plan_risk_aware,
    simulate_rollout,
)

st.set_page_config(page_title="DynNav Research Playground", page_icon="🧭", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1380px; padding-top: 1.25rem;}
    .small-note {color: #64748b; font-size: .9rem;}
    .hero-card, .decision-card, .contribution-card {
        border: 1px solid rgba(148,163,184,.35);
        border-radius: 16px;
        padding: 1rem 1.15rem;
        background: rgba(148,163,184,.07);
    }
    .contribution-card {min-height: 142px;}
    </style>
    """,
    unsafe_allow_html=True,
)

CONTRIBUTIONS = {
    "C01": ("Learned A*", "Learning-guided search and heuristic trade-offs"),
    "C02": ("Uncertainty estimation", "EKF/UKF-style uncertainty and calibration"),
    "C03": ("Risk-aware planning", "CVaR-style route selection"),
    "C04": ("Returnability", "Recoverability and irreversibility"),
    "C05": ("Safe-mode FSM", "Runtime supervision and safe-stop logic"),
    "C06": ("Energy & connectivity", "Mission feasibility under resource limits"),
    "C07": ("Next-best view", "Safe active exploration"),
    "C08": ("Security IDS", "Navigation anomaly and intrusion detection"),
    "C09": ("Multi-robot", "Coordination, belief sharing, and allocation"),
    "C10": ("Human-aware navigation", "Social costs and personal-space reasoning"),
    "C11": ("Twin-critic RL", "Dual-value reinforcement-learning analysis"),
    "C12": ("Diffusion occupancy", "Future occupancy prediction"),
    "C13": ("World model", "Latent dynamics and imagined rollouts"),
    "C14": ("Causal risk", "Structural causal risk attribution"),
    "C15": ("Neuromorphic sensing", "Event-driven perception"),
    "C16": ("Federated learning", "Distributed navigation learning"),
    "C17": ("Topological maps", "Semantic-topological planning"),
    "C18": ("CBF/STL shields", "Formal runtime safety constraints"),
    "C19": ("LLM mission planner", "Language instructions to structured missions"),
    "C20": ("Failure explainer", "Multimodal failure interpretation"),
    "C21": ("PPO navigation", "Policy optimisation playground"),
    "C22": ("Curriculum RL", "Progressive task difficulty"),
    "C23": ("Gaussian splatting", "Scene representation for navigation"),
    "C24": ("NeRF uncertainty", "Implicit mapping and uncertainty"),
    "C25": ("Adversarial simulator", "Robustness under navigation attacks"),
    "C26": ("BFT swarm", "Byzantine-resilient swarm consensus"),
}

st.title("🧭 DynNav Research Playground")
st.caption(
    "Explore the complete navigation loop or open any contribution and change its parameters interactively."
)
st.info(
    "Synthetic research visualization only. The graphics explain algorithms and controlled simulations; "
    "they are not ROS 2, hardware, field-validation, or certified-safety evidence."
)

with st.sidebar:
    st.header("Navigate")
    page = st.radio(
        "Dashboard page",
        ["🏠 Overview", "🤖 Closed-loop robot", "🧪 Contribution playground"],
        index=2,
    )

if page == "🏠 Overview":
    st.markdown(
        """
        <div class="hero-card">
        <h3>What happens inside DynNav?</h3>
        <p>Observation updates the occupancy belief. The system estimates uncertainty, risk,
        recoverability, connectivity, and resource margins. A planner proposes a route, the route
        monitor checks it online, and the supervisor chooses whether to continue, replan, enter a
        cautious state, recover, or stop.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(
        "observe → update belief → estimate uncertainty/risk → plan → monitor → "
        "continue/replan/recover/stop → record evidence",
        language="text",
    )
    st.subheader("Interactive research modules")
    items = list(CONTRIBUTIONS.items())
    for row_start in range(0, len(items), 3):
        cols = st.columns(3)
        for col, (code, (title, description)) in zip(cols, items[row_start : row_start + 3]):
            with col:
                st.markdown(
                    f'<div class="contribution-card"><strong>{code} — {title}</strong>'
                    f'<br><br>{description}</div>',
                    unsafe_allow_html=True,
                )
    st.stop()

if page == "🧪 Contribution playground":
    with st.sidebar:
        st.divider()
        selected = st.selectbox(
            "Choose contribution",
            list(CONTRIBUTIONS),
            format_func=lambda code: f"{code} — {CONTRIBUTIONS[code][0]}",
        )
        st.caption("Each contribution has its own controls, graphics, metrics, and interpretation.")

    title, description = CONTRIBUTIONS[selected]
    st.markdown(f"## {selected} — {title}")
    st.caption(description)
    renderer = RENDERERS.get(selected)
    if renderer is None:
        st.error(f"No dashboard renderer is registered for {selected}.")
    else:
        renderer(st)
    st.divider()
    st.markdown(
        '<p class="small-note">Change the sliders and controls to observe how assumptions alter '
        'paths, fields, decisions, metrics, or learned behaviour.</p>',
        unsafe_allow_html=True,
    )
    st.stop()

# Closed-loop robot page.
with st.sidebar:
    st.divider()
    st.header("Scenario controls")
    seed = st.number_input("Random seed", min_value=0, max_value=100_000, value=7, step=1)
    risk_weight = st.slider("Risk weight", 0.0, 6.0, 2.5, 0.1)
    planner_mode = st.radio("Planner", ["Risk-aware A*", "Classical A*"], index=0)
    dynamic_step_every = st.slider("Move obstacles every N steps", 1, 6, 2)
    show_uncertainty = st.checkbox("Overlay uncertainty", value=True)
    show_risk = st.checkbox("Overlay risk", value=True)
    show_baseline = st.checkbox("Show initial A* baseline", value=True)

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

frame_index = st.slider("Simulation step", 0, len(rollout.frames) - 1, 0)
frame = rollout.frames[frame_index]
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

metrics = st.columns(6)
metrics[0].metric("Step", frame.step)
metrics[1].metric("Supervisor", supervisor_state)
metrics[2].metric("Replans", frame.replan_count)
metrics[3].metric("Local risk", f"{local_risk:.3f}")
metrics[4].metric("Uncertainty", f"{local_uncertainty:.3f}")
metrics[5].metric("Path cells", len(frame.path_remaining))

live_tab, metrics_tab, pipeline_tab = st.tabs(["Live graphics", "Metrics", "Decision pipeline"])
with live_tab:
    plot_col, decision_col = st.columns([2.2, 1])
    with plot_col:
        fig, ax = plt.subplots(figsize=(9.5, 7.2))
        occupancy = np.clip(env.static + frame.dynamic_snapshot, 0, 1)
        ax.imshow(occupancy, origin="lower", cmap="Greys", alpha=0.90)
        if show_uncertainty:
            ax.imshow(env.uncertainty, origin="lower", cmap="Purples", alpha=0.25)
        if show_risk:
            ax.imshow(frame.risk_snapshot, origin="lower", cmap="Oranges", alpha=0.28)
        if show_baseline and baseline.path:
            bx, by = zip(*baseline.path)
            ax.plot(bx, by, "--", linewidth=1.5, label="Initial A* route")
        if frame.path_remaining:
            px, py = zip(*frame.path_remaining)
            ax.plot(px, py, linewidth=2.8, label="Active route")
        dyn_y, dyn_x = np.where(frame.dynamic_snapshot > 0.5)
        if len(dyn_x):
            ax.scatter(dyn_x, dyn_y, marker="s", s=38, label="Moving obstacle")
        ax.scatter(robot_x, robot_y, marker="o", s=130, label="Robot")
        ax.scatter(*cfg.goal, marker="*", s=180, label="Goal")
        ax.set_title(f"Closed-loop navigation — step {frame.step}")
        ax.set_aspect("equal")
        ax.legend(loc="upper left", fontsize=8)
        st.pyplot(fig, clear_figure=True)
    with decision_col:
        explanations = {
            "REPLAN": "A moving or newly observed obstacle compromised the route, so DynNav planned again.",
            "CAUTION": "The route remains available, but local risk or uncertainty is elevated.",
            "SAFE STOP": "No usable route is currently available, so the supervisor avoids unsafe motion.",
            "GOAL REACHED": "The robot reached its goal and the episode terminated.",
            "NORMAL": "The active path remains traversable and the monitored signals remain below caution thresholds.",
        }
        st.markdown(
            f'<div class="decision-card"><strong>{supervisor_state}</strong><br><br>'
            f'{explanations[supervisor_state]}</div>',
            unsafe_allow_html=True,
        )
        st.progress(min(max(local_risk, 0.0), 1.0), text=f"Risk: {local_risk:.3f}")
        st.progress(min(max(local_uncertainty, 0.0), 1.0), text=f"Uncertainty: {local_uncertainty:.3f}")
        st.write(f"Robot cell: `{frame.robot}`")
        st.write(f"Replanned now: `{'yes' if frame.replanned else 'no'}`")

with metrics_tab:
    st.dataframe(
        {
            "metric": ["success", "path cells", "expansions", "runtime ms", "cost", "average risk", "maximum risk"],
            "A*": [baseline.success, len(baseline.path), baseline.expansions, round(baseline.runtime_ms, 3), round(baseline.cost, 3), round(baseline.avg_risk, 3), round(baseline.max_risk, 3)],
            "Risk-aware A*": [risk_plan.success, len(risk_plan.path), risk_plan.expansions, round(risk_plan.runtime_ms, 3), round(risk_plan.cost, 3), round(risk_plan.avg_risk, 3), round(risk_plan.max_risk, 3)],
        },
        use_container_width=True,
        hide_index=True,
    )
    st.json({
        "reached_goal": rollout.reached_goal,
        "distance": round(rollout.total_distance, 3),
        "total_replans": rollout.total_replans,
        "average_risk": round(rollout.avg_risk, 3),
        "maximum_risk": round(rollout.max_risk, 3),
        "average_compute_ms": round(rollout.avg_compute_ms, 3),
    })

with pipeline_tab:
    st.markdown(
        """
        1. **Observe** the map and moving obstacles.
        2. **Estimate** occupancy uncertainty and spatial risk.
        3. **Plan** using geometric cost alone or geometric cost plus risk.
        4. **Monitor** the forward route for invalidation.
        5. **Decide** whether to continue, enter caution, replan, or stop.
        6. **Record** paths, timings, risk exposure, replans, and outcome.
        """
    )

st.divider()
st.markdown(
    '<p class="small-note">Install with <code>python -m pip install -e ".[dashboard]"</code> and run '
    '<code>streamlit run app/dashboard.py</code>.</p>',
    unsafe_allow_html=True,
)
