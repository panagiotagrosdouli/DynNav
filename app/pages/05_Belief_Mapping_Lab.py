from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import yaml

from dynnav.mapping.ros_map import load_ros_map
from dynnav.planners.astar import astar

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.simulation import build_environment

st.set_page_config(page_title="DynNav Belief & Mapping Lab", page_icon="🗺️", layout="wide")

st.title("Belief & Mapping Lab")
st.caption("Inspect how noisy observations update occupancy belief, uncertainty, entropy, and map coverage.")
st.info(
    "Synthetic interactive research environment. This page demonstrates deterministic Bayesian occupancy updates; "
    "it is not a ROS2 SLAM or hardware-validation result."
)

source_mode = st.radio(
    "Map source",
    ["Generated synthetic map", "Upload a real ROS occupancy map"],
    horizontal=True,
)
if source_mode == "Upload a real ROS occupancy map":
    st.markdown(
        "Upload the map-server YAML file and its referenced PGM/PNG image. "
        "Unknown cells are blocked by default; the route is a static-map A* baseline."
    )
    yaml_file = st.file_uploader("ROS map metadata (.yaml)", type=["yaml", "yml"])
    image_file = st.file_uploader("Occupancy image (.pgm or .png)", type=["pgm", "png"])
    if yaml_file is None or image_file is None:
        st.info("Choose both files to inspect a map.")
        st.link_button(
            "Download the official LILocBench occupancy-map ZIP",
            "https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/map_office.zip",
        )
        st.link_button(
            "Read the dataset details and license",
            "https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/",
        )
        st.stop()

    try:
        metadata = yaml.safe_load(yaml_file.getvalue())
        if not isinstance(metadata, dict):
            raise ValueError("map YAML must contain a metadata mapping")
        image_suffix = Path(image_file.name).suffix.lower()
        if image_suffix not in {".pgm", ".png"}:
            raise ValueError("map image must be a PGM or PNG file")
        with TemporaryDirectory(prefix="dynnav-ros-map-") as temp_dir:
            image_path = Path(temp_dir) / f"uploaded_map{image_suffix}"
            yaml_path = Path(temp_dir) / "uploaded_map.yaml"
            image_bytes = image_file.getvalue()
            image_path.write_bytes(image_bytes)
            metadata["image"] = image_path.name
            yaml_path.write_text(yaml.safe_dump(metadata), encoding="utf-8")
            ros_map = load_ros_map(yaml_path, unknown_as_obstacle=True)
            image_digest = sha256(image_bytes).hexdigest()
    except Exception as exc:
        st.error(f"Could not load this ROS map: {exc}")
        st.stop()

    grid = ros_map.grid
    if grid.width * grid.height > 1_000_000:
        st.error("This viewer is limited to maps with at most one million cells.")
        st.stop()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Map size", f"{grid.width} × {grid.height} cells")
    m2.metric("Resolution", f"{ros_map.resolution:.3f} m/cell")
    m3.metric("Occupied or unknown", f"{len(grid.obstacles):,} cells")
    m4.metric("Image SHA-256", image_digest[:12] + "…")
    st.caption(
        "The uploaded image is interpreted using the YAML origin, resolution, negate flag, and trinary thresholds. "
        "Unknown cells remain blocked. This is map and baseline-route validation, not a physical-robot result."
    )

    with st.sidebar:
        st.header("Route on uploaded map")
        start_x = st.slider("Start cell x", 0, grid.width - 1, min(grid.width - 2, max(0, grid.width // 10)))
        start_y = st.slider("Start cell y", 0, grid.height - 1, min(grid.height - 2, max(0, grid.height // 2)))
        goal_x = st.slider("Goal cell x", 0, grid.width - 1, min(grid.width - 1, max(0, grid.width * 9 // 10)))
        goal_y = st.slider("Goal cell y", 0, grid.height - 1, min(grid.height - 1, max(0, grid.height // 2)))

    start, goal = (start_x, start_y), (goal_x, goal_y)
    route = None
    if not grid.passable(start):
        st.warning("The start cell is occupied or unknown.")
    elif not grid.passable(goal):
        st.warning("The goal cell is occupied or unknown.")
    else:
        route = astar(grid, start, goal)
        if route.success:
            st.success(
                f"Static route found: {route.cost * ros_map.resolution:.2f} m, "
                f"{route.nodes_expanded:,} cells expanded, {route.planning_time_ms:.2f} ms."
            )
        else:
            st.warning("No static route connects the selected cells.")

    occupancy = np.zeros((grid.height, grid.width), dtype=np.uint8)
    for cell_x, cell_y in grid.obstacles:
        occupancy[cell_y, cell_x] = 1
    fig = go.Figure(
        go.Heatmap(
            z=occupancy,
            x=list(range(grid.width)),
            y=list(range(grid.height)),
            zmin=0,
            zmax=1,
            colorscale=[[0, "#fff7fb"], [1, "#d63384"]],
            showscale=False,
            hovertemplate="cell (%{x}, %{y})<extra></extra>",
        )
    )
    if route and route.success:
        path_x, path_y = zip(*route.path)
        fig.add_trace(go.Scatter(x=path_x, y=path_y, mode="lines", name="A* path", line={"color": "#6f42c1", "width": 3}))
    fig.add_trace(go.Scatter(x=[start_x], y=[start_y], mode="markers", name="Start", marker={"color": "#2563eb", "size": 10}))
    fig.add_trace(go.Scatter(x=[goal_x], y=[goal_y], mode="markers", name="Goal", marker={"color": "#dc2626", "size": 12, "symbol": "star"}))
    fig.update_layout(title="ROS occupancy map and baseline route (pink occupancy)", xaxis_title="Cell x", yaxis_title="Cell y", yaxis={"scaleanchor": "x"})
    st.plotly_chart(fig, use_container_width=True)
    st.link_button(
        "Download the official LILocBench occupancy-map ZIP",
        "https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/map_office.zip",
    )
    st.link_button(
        "Read the dataset details and license",
        "https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/",
    )
    st.caption(
        "LILocBench data are licensed CC BY-NC-SA. Attribute the dataset, retain its license terms, "
        "and do not commit the downloaded files to this repository."
    )
    st.stop()

with st.sidebar:
    st.header("Observation model")
    seed = st.number_input("Map seed", min_value=0, max_value=100_000, value=7, step=1)
    prior = st.slider("Prior occupancy probability", 0.05, 0.95, 0.50, 0.01)
    p_hit = st.slider("Sensor hit probability", 0.51, 0.99, 0.90, 0.01)
    p_miss = st.slider("Sensor miss probability", 0.01, 0.49, 0.15, 0.01)
    sensor_range = st.slider("Sensor range (cells)", 2, 18, 8)
    false_positive = st.slider("False-positive rate", 0.0, 0.30, 0.04, 0.01)
    false_negative = st.slider("False-negative rate", 0.0, 0.30, 0.06, 0.01)
    evidence_decay = st.slider("Evidence decay", 0.0, 0.25, 0.02, 0.01)
    robot_x = st.slider("Robot x", 1, DEFAULT_SCENARIO.grid_size - 2, DEFAULT_SCENARIO.start[0])
    robot_y = st.slider("Robot y", 1, DEFAULT_SCENARIO.grid_size - 2, DEFAULT_SCENARIO.start[1])

cfg = replace(DEFAULT_SCENARIO, random_seed=int(seed), sensing_radius=int(sensor_range))
env = build_environment(cfg, seed=int(seed))
ground_truth = np.clip(env.static + env.dynamic, 0, 1).astype(float)
height, width = ground_truth.shape

prior_map = np.full_like(ground_truth, float(prior), dtype=float)
yy, xx = np.indices(ground_truth.shape)
visible = (xx - robot_x) ** 2 + (yy - robot_y) ** 2 <= sensor_range**2

rng = np.random.default_rng(int(seed) + int(robot_x) * 1009 + int(robot_y) * 9176)
observed = ground_truth.copy()
free_flip = (ground_truth < 0.5) & (rng.random(ground_truth.shape) < false_positive)
occupied_flip = (ground_truth >= 0.5) & (rng.random(ground_truth.shape) < false_negative)
observed[free_flip] = 1.0
observed[occupied_flip] = 0.0

posterior = prior_map.copy()
occupied_obs = visible & (observed >= 0.5)
free_obs = visible & ~occupied_obs

# Binary Bayes update using the selected sensor model.
def bayes_update(p: np.ndarray, likelihood_occ: float, likelihood_free: float) -> np.ndarray:
    numerator = likelihood_occ * p
    denominator = numerator + likelihood_free * (1.0 - p)
    return numerator / np.maximum(denominator, 1e-12)

posterior[occupied_obs] = bayes_update(prior_map[occupied_obs], p_hit, p_miss)
posterior[free_obs] = bayes_update(prior_map[free_obs], 1.0 - p_hit, 1.0 - p_miss)
posterior = (1.0 - evidence_decay) * posterior + evidence_decay * prior
posterior = np.clip(posterior, 1e-6, 1.0 - 1e-6)

entropy_before = -(prior_map * np.log2(prior_map) + (1 - prior_map) * np.log2(1 - prior_map))
entropy_after = -(posterior * np.log2(posterior) + (1 - posterior) * np.log2(1 - posterior))
uncertainty = 4.0 * posterior * (1.0 - posterior)
coverage = float(visible.mean())
mean_entropy_before = float(entropy_before.mean())
mean_entropy_after = float(entropy_after.mean())
information_gain = mean_entropy_before - mean_entropy_after

m1, m2, m3, m4 = st.columns(4)
m1.metric("Observed coverage", f"{100 * coverage:.1f}%")
m2.metric("Mean entropy before", f"{mean_entropy_before:.3f} bits")
m3.metric("Mean entropy after", f"{mean_entropy_after:.3f} bits")
m4.metric("Information gain", f"{information_gain:.3f} bits")

labels = [
    (ground_truth, "Ground truth (evaluation only)", "Greys"),
    (prior_map, "Prior occupancy belief", "Viridis"),
    (posterior, "Posterior occupancy belief", "Viridis"),
    (uncertainty, "Posterior uncertainty", "Magma"),
]
cols = st.columns(2)
for index, (data, title, scale) in enumerate(labels):
    with cols[index % 2]:
        fig = go.Figure(go.Heatmap(z=data, colorscale=scale, zmin=0, zmax=1, colorbar={"title": title}))
        fig.add_trace(
            go.Scatter(
                x=[robot_x],
                y=[robot_y],
                mode="markers",
                marker={"size": 13, "symbol": "triangle-up"},
                name="Robot",
            )
        )
        fig.update_layout(title=title, height=430, margin=dict(l=20, r=20, t=55, b=20), yaxis_scaleanchor="x")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Why did belief change?")
if information_gain > 0:
    st.success(
        f"The sensor footprint covered {100 * coverage:.1f}% of the map. Occupied observations moved cells toward "
        f"p(occupied)={float(bayes_update(np.array([prior]), p_hit, p_miss)[0]):.3f}, while free observations moved "
        f"them toward p(occupied)={float(bayes_update(np.array([prior]), 1-p_hit, 1-p_miss)[0]):.3f}. "
        f"The resulting mean entropy reduction is {information_gain:.3f} bits."
    )
else:
    st.warning("The selected observation parameters did not reduce mean entropy for this configuration.")

st.subheader("Cell inspector")
inspect_x = st.slider("Inspect x", 0, width - 1, robot_x, key="belief_inspect_x")
inspect_y = st.slider("Inspect y", 0, height - 1, robot_y, key="belief_inspect_y")
st.json(
    {
        "cell": [inspect_x, inspect_y],
        "visible": bool(visible[inspect_y, inspect_x]),
        "ground_truth_occupied": bool(ground_truth[inspect_y, inspect_x] >= 0.5),
        "observed_occupied": bool(observed[inspect_y, inspect_x] >= 0.5) if visible[inspect_y, inspect_x] else None,
        "prior_probability": round(float(prior_map[inspect_y, inspect_x]), 6),
        "posterior_probability": round(float(posterior[inspect_y, inspect_x]), 6),
        "posterior_uncertainty": round(float(uncertainty[inspect_y, inspect_x]), 6),
        "entropy_before_bits": round(float(entropy_before[inspect_y, inspect_x]), 6),
        "entropy_after_bits": round(float(entropy_after[inspect_y, inspect_x]), 6),
    }
)
