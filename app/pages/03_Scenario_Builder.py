from __future__ import annotations

from dataclasses import asdict, replace

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import yaml

from dynnav_dashboard.config import DEFAULT_SCENARIO, ScenarioConfig
from dynnav_dashboard.simulation import build_environment

st.set_page_config(page_title="DynNav Scenario Builder", page_icon="🗺️", layout="wide")
st.title("Scenario Builder")
st.caption("Create a deterministic synthetic navigation scenario, inspect it, and export a reproducible YAML configuration.")
st.info(
    "Synthetic interactive research environment. Scenario previews do not establish ROS2, Gazebo, hardware, or formal-safety validation."
)

if "scenario_builder" not in st.session_state:
    st.session_state.scenario_builder = asdict(DEFAULT_SCENARIO)

presets = {
    "Default laboratory": dict(grid_size=40, n_static_obstacles=14, n_dynamic_obstacles=3, risk_weight=2.5, random_seed=7),
    "Narrow passage": dict(grid_size=36, n_static_obstacles=22, n_dynamic_obstacles=1, risk_weight=3.5, random_seed=19),
    "Dynamic crossing": dict(grid_size=42, n_static_obstacles=10, n_dynamic_obstacles=6, risk_weight=3.0, random_seed=31),
    "High uncertainty": dict(grid_size=40, n_static_obstacles=12, n_dynamic_obstacles=2, risk_weight=4.5, random_seed=11),
    "Blocked shortcut": dict(grid_size=34, n_static_obstacles=18, n_dynamic_obstacles=4, risk_weight=2.0, random_seed=43),
}

with st.sidebar:
    st.header("Scenario controls")
    preset_name = st.selectbox("Preset", list(presets), key="scenario_preset")
    if st.button("Apply preset", use_container_width=True):
        st.session_state.scenario_builder.update(presets[preset_name])
        size = int(st.session_state.scenario_builder["grid_size"])
        st.session_state.scenario_builder["start"] = (2, 2)
        st.session_state.scenario_builder["goal"] = (size - 3, size - 3)
        st.rerun()

    current = st.session_state.scenario_builder
    grid_size = st.slider("Map size", 20, 70, int(current["grid_size"]), key="sb_grid")
    n_static = st.slider("Static obstacles", 0, 40, int(current["n_static_obstacles"]), key="sb_static")
    n_dynamic = st.slider("Dynamic obstacles", 0, 12, int(current["n_dynamic_obstacles"]), key="sb_dynamic")
    min_size = st.slider("Obstacle minimum size", 1, 6, int(current["obstacle_min_size"]), key="sb_min")
    max_size = st.slider("Obstacle maximum size", min_size, 10, max(min_size, int(current["obstacle_max_size"])), key="sb_max")
    sensing = st.slider("Sensor range", 1, 15, int(current["sensing_radius"]), key="sb_sense")
    uncertainty_sigma = st.slider("Uncertainty spread", 0.5, 10.0, float(current["uncertainty_sigma"]), 0.25, key="sb_sigma")
    risk_weight = st.slider("Risk weight", 0.0, 8.0, float(current["risk_weight"]), 0.1, key="sb_risk")
    seed = st.number_input("Seed", min_value=0, max_value=100_000, value=int(current["random_seed"]), key="sb_seed")

start_default = tuple(st.session_state.scenario_builder.get("start", (2, 2)))
goal_default = tuple(st.session_state.scenario_builder.get("goal", (grid_size - 3, grid_size - 3)))

coords_a, coords_b = st.columns(2)
with coords_a:
    start_x = st.number_input("Start x", 0, grid_size - 1, min(int(start_default[0]), grid_size - 1), key="sb_start_x")
    start_y = st.number_input("Start y", 0, grid_size - 1, min(int(start_default[1]), grid_size - 1), key="sb_start_y")
with coords_b:
    goal_x = st.number_input("Goal x", 0, grid_size - 1, min(int(goal_default[0]), grid_size - 1), key="sb_goal_x")
    goal_y = st.number_input("Goal y", 0, grid_size - 1, min(int(goal_default[1]), grid_size - 1), key="sb_goal_y")

config = replace(
    DEFAULT_SCENARIO,
    grid_size=int(grid_size),
    start=(int(start_x), int(start_y)),
    goal=(int(goal_x), int(goal_y)),
    n_static_obstacles=int(n_static),
    n_dynamic_obstacles=int(n_dynamic),
    obstacle_min_size=int(min_size),
    obstacle_max_size=int(max_size),
    sensing_radius=int(sensing),
    uncertainty_sigma=float(uncertainty_sigma),
    risk_weight=float(risk_weight),
    random_seed=int(seed),
)

validation_errors: list[str] = []
if config.start == config.goal:
    validation_errors.append("Start and goal must be different.")
if config.obstacle_min_size > config.obstacle_max_size:
    validation_errors.append("Obstacle minimum size cannot exceed maximum size.")
if n_static * max_size * max_size > grid_size * grid_size * 0.75:
    validation_errors.append("The obstacle configuration is likely too dense for a usable map.")

if validation_errors:
    for error in validation_errors:
        st.error(error)
    st.stop()

env = build_environment(config, seed=config.random_seed)
config_dict = asdict(config)
config_dict["start"] = list(config.start)
config_dict["goal"] = list(config.goal)
st.session_state.scenario_builder = config_dict
st.session_state.active_scenario = config_dict

preview, editor = st.columns([1.5, 1])
with preview:
    st.subheader("Scenario preview")
    fig, ax = plt.subplots(figsize=(8, 7))
    occupancy = np.clip(env.static + env.dynamic, 0, 1)
    ax.imshow(occupancy, origin="lower", cmap="Greys", alpha=0.95)
    ax.imshow(env.uncertainty, origin="lower", cmap="Purples", alpha=0.22)
    ax.scatter(*config.start, marker="o", s=100, label="Start")
    ax.scatter(*config.goal, marker="*", s=180, label="Goal")
    ax.set_title(f"Seed {config.random_seed} · {config.grid_size}×{config.grid_size}")
    ax.set_aspect("equal")
    ax.legend(loc="upper left")
    st.pyplot(fig, clear_figure=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Static cells", int(env.static.sum()))
    m2.metric("Dynamic cells", int(env.dynamic.sum()))
    m3.metric("Mean uncertainty", f"{float(env.uncertainty.mean()):.3f}")
    m4.metric("Free-space ratio", f"{float((occupancy < 0.5).mean()):.1%}")

with editor:
    st.subheader("YAML editor")
    yaml_text = yaml.safe_dump(config_dict, sort_keys=False)
    edited_yaml = st.text_area("Resolved scenario", yaml_text, height=390, key="sb_yaml")
    try:
        loaded = yaml.safe_load(edited_yaml)
        if not isinstance(loaded, dict):
            raise ValueError("YAML root must be a mapping")
        ScenarioConfig(**{**asdict(DEFAULT_SCENARIO), **loaded, "start": tuple(loaded.get("start", config.start)), "goal": tuple(loaded.get("goal", config.goal))})
        st.success("YAML structure is valid.")
    except Exception as exc:
        st.error(f"YAML validation failed: {exc}")

    st.download_button(
        "Download scenario YAML",
        data=yaml_text,
        file_name=f"dynnav_scenario_seed_{config.random_seed}.yaml",
        mime="application/yaml",
        use_container_width=True,
    )
    st.download_button(
        "Download configuration JSON",
        data=__import__("json").dumps(config_dict, indent=2),
        file_name=f"dynnav_scenario_seed_{config.random_seed}.json",
        mime="application/json",
        use_container_width=True,
    )
    if st.button("Reset to defaults", use_container_width=True):
        st.session_state.scenario_builder = asdict(DEFAULT_SCENARIO)
        st.rerun()

st.caption("The active scenario is stored in Streamlit session state for use by other laboratory pages in this session.")
