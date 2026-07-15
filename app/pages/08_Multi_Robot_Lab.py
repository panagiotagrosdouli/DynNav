from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="DynNav Multi-Robot Lab", page_icon="MR", layout="wide")
st.title("Multi-Robot Lab")
st.caption("Synthetic fleet coordination, communication, route-conflict, and task-progress explorer.")
st.info("Research prototype: this page is a deterministic synthetic coordination model, not a validated fleet controller.")

with st.sidebar:
    st.header("Fleet controls")
    n_robots = st.slider("Robots", 2, 6, 4)
    frame = st.slider("Simulation frame", 0, 100, 30)
    communication_range = st.slider("Communication range", 2.0, 30.0, 12.0, 0.5)
    packet_loss = st.slider("Packet loss", 0.0, 0.9, 0.15, 0.05)
    conflict_distance = st.slider("Conflict distance", 0.5, 5.0, 1.8, 0.1)
    seed = st.number_input("Seed", 0, 10000, 11)

rng = np.random.default_rng(int(seed))
starts = np.array([[2, 2], [28, 2], [2, 28], [28, 28], [15, 2], [15, 28]], dtype=float)[:n_robots]
goals = np.array([[28, 28], [2, 28], [28, 2], [2, 2], [15, 28], [15, 2]], dtype=float)[:n_robots]
progress = np.clip(frame / 100.0, 0.0, 1.0)
positions = starts + (goals - starts) * progress

# Deterministic lateral offsets avoid every route being identical while preserving reproducibility.
offsets = rng.uniform(-2.0, 2.0, size=n_robots)
paths = []
for i in range(n_robots):
    t = np.linspace(0.0, 1.0, 101)
    base = starts[i][None, :] + (goals[i] - starts[i])[None, :] * t[:, None]
    perpendicular = np.array([-(goals[i] - starts[i])[1], (goals[i] - starts[i])[0]], dtype=float)
    norm = np.linalg.norm(perpendicular)
    if norm:
        perpendicular /= norm
    bend = np.sin(np.pi * t)[:, None] * perpendicular[None, :] * offsets[i]
    paths.append(base + bend)
    positions[i] = paths[-1][frame]

links = []
conflicts = []
for i, j in itertools.combinations(range(n_robots), 2):
    distance = float(np.linalg.norm(positions[i] - positions[j]))
    delivered = ((i + 1) * (j + 3) * (frame + 7) % 100) / 100.0 >= packet_loss
    if distance <= communication_range and delivered:
        links.append((i, j, distance))
    if distance <= conflict_distance:
        conflicts.append((i, j, distance))

fig = go.Figure()
for i, path in enumerate(paths):
    name = f"Robot {i + 1}"
    fig.add_trace(go.Scatter(x=path[:, 0], y=path[:, 1], mode="lines", name=f"{name} route"))
    fig.add_trace(go.Scatter(x=[positions[i, 0]], y=[positions[i, 1]], mode="markers+text", text=[f"R{i+1}"], textposition="top center", marker={"size": 16}, name=name, showlegend=False))
    fig.add_trace(go.Scatter(x=[goals[i, 0]], y=[goals[i, 1]], mode="markers", marker={"symbol": "star", "size": 11}, name=f"R{i+1} goal", showlegend=False))
for i, j, distance in links:
    fig.add_trace(go.Scatter(x=[positions[i, 0], positions[j, 0]], y=[positions[i, 1], positions[j, 1]], mode="lines", line={"dash": "dot", "width": 1}, name=f"link R{i+1}-R{j+1} ({distance:.1f})", showlegend=False))
for i, j, _ in conflicts:
    midpoint = (positions[i] + positions[j]) / 2
    fig.add_trace(go.Scatter(x=[midpoint[0]], y=[midpoint[1]], mode="markers", marker={"symbol": "x", "size": 18}, name="Route conflict", showlegend=False))
fig.update_xaxes(range=[0, 30], title="x")
fig.update_yaxes(range=[0, 30], title="y", scaleanchor="x", scaleratio=1)
fig.update_layout(height=650, legend={"orientation": "h"})

m1, m2, m3, m4 = st.columns(4)
m1.metric("Robots", n_robots)
m2.metric("Active links", len(links))
m3.metric("Current conflicts", len(conflicts))
m4.metric("Mission progress", f"{100 * progress:.0f}%")

left, right = st.columns([1.7, 1])
with left:
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Fleet status")
    rows = []
    for i in range(n_robots):
        degree = sum(i in (a, b) for a, b, _ in links)
        conflict_count = sum(i in (a, b) for a, b, _ in conflicts)
        remaining = float(np.linalg.norm(goals[i] - positions[i]))
        rows.append({
            "robot": f"R{i+1}",
            "x": round(float(positions[i, 0]), 2),
            "y": round(float(positions[i, 1]), 2),
            "remaining": round(remaining, 2),
            "communication_links": degree,
            "conflicts": conflict_count,
            "task": f"Reach ({int(goals[i,0])}, {int(goals[i,1])})",
        })
    status = pd.DataFrame(rows)
    st.dataframe(status, hide_index=True, use_container_width=True)
    if conflicts:
        conflict_text = ", ".join(f"R{i+1}–R{j+1}: {d:.2f}" for i, j, d in conflicts)
        st.warning(f"Separation threshold crossed: {conflict_text} cells.")
    else:
        st.success("No current robot pair is inside the configured conflict distance.")
    st.write(
        f"At frame {frame}, {len(links)} communication links are available after applying range "
        f"{communication_range:.1f} and packet-loss setting {packet_loss:.2f}."
    )
    st.download_button("Download fleet status CSV", status.to_csv(index=False), "multi_robot_status.csv", "text/csv")

st.subheader("Communication links")
link_table = pd.DataFrame([
    {"source": f"R{i+1}", "target": f"R{j+1}", "distance": round(distance, 3)}
    for i, j, distance in links
])
st.dataframe(link_table, hide_index=True, use_container_width=True)
