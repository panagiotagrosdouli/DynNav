from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="DynNav Dynamic Obstacles", page_icon="↗", layout="wide")
st.title("Dynamic Obstacle Lab")
st.caption("Inspect observed motion, prediction uncertainty, closest approach, and route conflict diagnostics.")
st.info("Synthetic interactive research environment. Predictions are explanatory software outputs, not physical-robot safety guarantees.")

with st.sidebar:
    st.header("Obstacle model")
    behavior = st.selectbox("Behavior", ["Crossing", "Constant velocity", "Stop-and-go", "Waypoint", "Random walk"])
    horizon = st.slider("Prediction horizon", 4, 30, 14)
    speed = st.slider("Obstacle speed", 0.1, 2.0, 0.8, 0.1)
    uncertainty_growth = st.slider("Uncertainty growth", 0.0, 0.5, 0.12, 0.01)
    frame = st.slider("Observed frame", 0, 30, 8)
    seed = st.number_input("Seed", 0, 10000, 7)

rng = np.random.default_rng(int(seed))
robot_start = np.array([2.0, 2.0])
robot_goal = np.array([28.0, 28.0])
robot_path = np.linspace(robot_start, robot_goal, 80)


def obstacle_position(t: float) -> np.ndarray:
    if behavior == "Crossing":
        return np.array([15.0, 2.0 + speed * t])
    if behavior == "Constant velocity":
        return np.array([4.0 + speed * t, 22.0 - 0.25 * speed * t])
    if behavior == "Stop-and-go":
        active = max(0.0, t - 4.0 * math.floor(t / 8.0))
        return np.array([5.0 + speed * (4.0 * math.floor(t / 8.0) + min(active, 4.0)), 16.0])
    if behavior == "Waypoint":
        phase = (speed * t) % 40.0
        if phase < 10:
            return np.array([8.0 + phase, 8.0])
        if phase < 20:
            return np.array([18.0, 8.0 + phase - 10])
        if phase < 30:
            return np.array([18.0 - (phase - 20), 18.0])
        return np.array([8.0, 18.0 - (phase - 30)])
    # Deterministic pseudo-random walk generated from the seed and time index.
    steps = rng.normal(0.0, speed, size=(max(int(t) + 1, 1), 2))
    return np.clip(np.array([14.0, 14.0]) + steps.sum(axis=0), 1.0, 29.0)

observed = obstacle_position(float(frame))
predicted = np.array([obstacle_position(float(frame + i)) for i in range(horizon + 1)])
sigmas = 0.25 + uncertainty_growth * np.arange(horizon + 1)

robot_index = min(frame * 2, len(robot_path) - 1)
robot = robot_path[robot_index]
future_robot = robot_path[robot_index : min(robot_index + horizon + 1, len(robot_path))]
paired = min(len(future_robot), len(predicted))
distances = np.linalg.norm(future_robot[:paired] - predicted[:paired], axis=1)
closest_idx = int(np.argmin(distances)) if paired else 0
closest_distance = float(distances[closest_idx]) if paired else float("nan")
time_to_conflict = closest_idx if paired and closest_distance < 2.0 else None

m1, m2, m3, m4 = st.columns(4)
m1.metric("Closest predicted approach", f"{closest_distance:.2f} cells")
m2.metric("Conflict horizon", "none" if time_to_conflict is None else f"{time_to_conflict} steps")
m3.metric("Current obstacle speed", f"{speed:.1f} cells/step")
m4.metric("Final prediction σ", f"{sigmas[-1]:.2f}")

left, right = st.columns([1.7, 1])
with left:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=robot_path[:, 0], y=robot_path[:, 1], mode="lines", name="Robot route"))
    fig.add_trace(go.Scatter(x=[robot[0]], y=[robot[1]], mode="markers", marker={"size": 15}, name="Robot"))
    fig.add_trace(go.Scatter(x=predicted[:, 0], y=predicted[:, 1], mode="lines+markers", name="Obstacle prediction"))
    fig.add_trace(go.Scatter(x=[observed[0]], y=[observed[1]], mode="markers", marker={"size": 16, "symbol": "x"}, name="Observed obstacle"))
    for i, (point, sigma) in enumerate(zip(predicted, sigmas)):
        fig.add_shape(type="circle", x0=point[0]-sigma, x1=point[0]+sigma, y0=point[1]-sigma, y1=point[1]+sigma, line={"width": 1}, opacity=0.22)
    if paired:
        fig.add_trace(go.Scatter(x=[future_robot[closest_idx, 0], predicted[closest_idx, 0]], y=[future_robot[closest_idx, 1], predicted[closest_idx, 1]], mode="lines", name="Closest approach"))
    fig.update_xaxes(range=[0, 30], title="x")
    fig.update_yaxes(range=[0, 30], title="y", scaleanchor="x", scaleratio=1)
    fig.update_layout(height=650, legend={"orientation": "h"})
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Prediction diagnostics")
    table = pd.DataFrame({
        "step_ahead": np.arange(horizon + 1),
        "predicted_x": predicted[:, 0],
        "predicted_y": predicted[:, 1],
        "uncertainty_sigma": sigmas,
    })
    st.dataframe(table, hide_index=True, use_container_width=True, height=330)
    if time_to_conflict is None:
        st.success(f"No predicted separation below 2.0 cells. Minimum is {closest_distance:.2f} cells.")
    else:
        st.warning(f"Predicted route conflict in {time_to_conflict} steps: separation {closest_distance:.2f} cells.")
    st.markdown("**Grounded explanation**")
    st.write(
        f"The selected {behavior.lower()} model projects the obstacle for {horizon} steps. "
        f"Prediction uncertainty grows from {sigmas[0]:.2f} to {sigmas[-1]:.2f}. "
        f"The smallest robot–obstacle separation is {closest_distance:.2f} cells."
    )
    st.download_button("Download prediction CSV", table.to_csv(index=False), "dynamic_obstacle_prediction.csv", "text/csv")
