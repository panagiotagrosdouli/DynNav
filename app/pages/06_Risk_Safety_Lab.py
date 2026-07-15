from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.simulation import build_environment, plan_astar, plan_risk_aware

st.set_page_config(page_title="DynNav Risk & Safety Lab", page_icon="🛡️", layout="wide")

st.title("Risk & Safety Lab")
st.caption("Compose transparent risk layers and inspect how thresholds alter routing and supervisor decisions.")
st.info(
    "Synthetic interactive research environment. Threshold states and risk maps shown here are explanatory software "
    "outputs, not certified physical-robot safety guarantees."
)

with st.sidebar:
    st.header("Scenario")
    seed = st.number_input("Map seed", min_value=0, max_value=100_000, value=7, step=1)
    obstacle_count = st.slider("Static obstacles", 4, 28, DEFAULT_SCENARIO.n_static_obstacles)
    dynamic_count = st.slider("Dynamic obstacles", 0, 8, DEFAULT_SCENARIO.n_dynamic_obstacles)
    st.header("Risk composition")
    obstacle_weight = st.slider("Obstacle risk weight", 0.0, 5.0, 2.5, 0.1)
    uncertainty_weight = st.slider("Uncertainty risk weight", 0.0, 5.0, 1.5, 0.1)
    unknown_weight = st.slider("Unknown-space risk weight", 0.0, 5.0, 1.0, 0.1)
    narrow_weight = st.slider("Narrow-passage risk weight", 0.0, 5.0, 1.2, 0.1)
    st.header("Supervisor thresholds")
    warning_threshold = st.slider("Warning threshold", 0.05, 0.95, 0.45, 0.01)
    replan_threshold = st.slider("Replan threshold", 0.05, 1.00, 0.65, 0.01)
    stop_threshold = st.slider("Stop threshold", 0.05, 1.00, 0.85, 0.01)
    minimum_clearance = st.slider("Minimum clearance (cells)", 0.0, 6.0, 1.5, 0.1)

if not warning_threshold <= replan_threshold <= stop_threshold:
    st.error("Thresholds must satisfy warning ≤ replan ≤ stop.")
    st.stop()

cfg = replace(
    DEFAULT_SCENARIO,
    random_seed=int(seed),
    n_static_obstacles=int(obstacle_count),
    n_dynamic_obstacles=int(dynamic_count),
)
env = build_environment(cfg, seed=int(seed))
occupancy = np.clip(env.static + env.dynamic, 0, 1)

# Derive transparent synthetic layers from actual environment arrays.
obstacle_layer = np.asarray(env.risk, dtype=float)
uncertainty_layer = np.asarray(env.uncertainty, dtype=float)
unknown_layer = np.clip(uncertainty_layer ** 1.5, 0, 1)

# Approximate narrow-passage pressure from free-neighbour count.
free = occupancy < 0.5
neighbour_count = np.zeros_like(occupancy, dtype=float)
for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
    shifted = np.roll(np.roll(free, dy, axis=0), dx, axis=1)
    neighbour_count += shifted
narrow_layer = np.where(free, np.clip((3.0 - neighbour_count) / 3.0, 0, 1), 1.0)

weight_sum = max(obstacle_weight + uncertainty_weight + unknown_weight + narrow_weight, 1e-9)
combined = (
    obstacle_weight * obstacle_layer
    + uncertainty_weight * uncertainty_layer
    + unknown_weight * unknown_layer
    + narrow_weight * narrow_layer
) / weight_sum
combined = np.clip(combined, 0, 1)

baseline = plan_astar(env, cfg.start, cfg.goal)
risk_plan = plan_risk_aware(env, cfg.start, cfg.goal, float(weight_sum))
active_path = risk_plan.path if risk_plan.success else baseline.path

if active_path:
    path_values = np.array([combined[y, x] for x, y in active_path], dtype=float)
    mean_route_risk = float(path_values.mean())
    max_route_risk = float(path_values.max())
else:
    path_values = np.array([], dtype=float)
    mean_route_risk = 1.0
    max_route_risk = 1.0

if not active_path or max_route_risk >= stop_threshold:
    supervisor = "SAFE STOP"
    action = "Stop and wait for a safer route or new observation."
elif max_route_risk >= replan_threshold:
    supervisor = "REPLAN"
    action = "Reject the current route and request replanning."
elif max_route_risk >= warning_threshold:
    supervisor = "CAUTION"
    action = "Continue conservatively while monitoring risk."
else:
    supervisor = "NORMAL"
    action = "Continue on the selected route."

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Supervisor", supervisor)
m2.metric("Mean route risk", f"{mean_route_risk:.3f}")
m3.metric("Maximum route risk", f"{max_route_risk:.3f}")
m4.metric("Route cells", len(active_path))
m5.metric("Risk-aware success", "yes" if risk_plan.success else "no")

layers = [
    (obstacle_layer, "Obstacle proximity risk"),
    (uncertainty_layer, "Uncertainty risk"),
    (unknown_layer, "Unknown-space proxy risk"),
    (narrow_layer, "Narrow-passage risk"),
    (combined, "Combined risk"),
]

cols = st.columns(2)
for index, (layer, title) in enumerate(layers):
    with cols[index % 2]:
        fig = go.Figure(go.Heatmap(z=layer, colorscale="Turbo", zmin=0, zmax=1, colorbar={"title": "risk"}))
        if title == "Combined risk":
            if baseline.path:
                bx, by = zip(*baseline.path)
                fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", name="Shortest path", line={"dash": "dash"}))
            if active_path:
                px, py = zip(*active_path)
                fig.add_trace(go.Scatter(x=px, y=py, mode="lines", name="Selected route", line={"width": 4}))
            fig.add_trace(go.Scatter(x=[cfg.start[0]], y=[cfg.start[1]], mode="markers", name="Start"))
            fig.add_trace(go.Scatter(x=[cfg.goal[0]], y=[cfg.goal[1]], mode="markers", name="Goal"))
        fig.update_layout(title=title, height=430, margin=dict(l=20, r=20, t=55, b=20), yaxis_scaleanchor="x")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Why did the supervisor choose this state?")
st.write(
    f"The selected route has maximum combined risk **{max_route_risk:.3f}**. The configured thresholds are "
    f"warning={warning_threshold:.2f}, replan={replan_threshold:.2f}, and stop={stop_threshold:.2f}. "
    f"Therefore the supervisor state is **{supervisor}**. {action}"
)

if active_path:
    contributions = []
    for name, layer, weight in [
        ("Obstacle", obstacle_layer, obstacle_weight),
        ("Uncertainty", uncertainty_layer, uncertainty_weight),
        ("Unknown space", unknown_layer, unknown_weight),
        ("Narrow passage", narrow_layer, narrow_weight),
    ]:
        values = np.array([layer[y, x] for x, y in active_path], dtype=float)
        contributions.append(
            {
                "risk_source": name,
                "weight": weight,
                "mean_on_route": float(values.mean()),
                "weighted_mean": float(weight * values.mean() / weight_sum),
                "maximum_on_route": float(values.max()),
            }
        )
    contribution_df = pd.DataFrame(contributions).sort_values("weighted_mean", ascending=False)
    st.subheader("Route risk decomposition")
    st.dataframe(contribution_df, use_container_width=True, hide_index=True)
    dominant = contribution_df.iloc[0]
    st.info(
        f"Dominant route-risk source: {dominant['risk_source']} "
        f"(weighted mean contribution {dominant['weighted_mean']:.3f})."
    )

st.subheader("Threshold counterfactual")
threshold_grid = np.linspace(0.05, 1.0, 96)
first_acceptable = next((float(t) for t in threshold_grid if max_route_risk < t), None)
if first_acceptable is None:
    st.warning("The route remains above every tested acceptance threshold.")
else:
    st.write(
        f"The route first becomes acceptable under a simple maximum-risk rule when the acceptance threshold exceeds "
        f"approximately **{first_acceptable:.2f}**. This is a diagnostic counterfactual, not a safety recommendation."
    )

st.download_button(
    "Download risk decomposition CSV",
    contribution_df.to_csv(index=False) if active_path else "risk_source,weight,mean_on_route,weighted_mean,maximum_on_route\n",
    file_name=f"dynnav_risk_decomposition_seed_{seed}.csv",
    mime="text/csv",
)
