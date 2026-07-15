from __future__ import annotations

import importlib.util
import platform
import shutil
import sys

import streamlit as st

from dynnav_dashboard.contributions import RENDERERS
from dynnav_dashboard.registry import load_contribution_registry

st.set_page_config(page_title="DynNav System Status", page_icon="🧪", layout="wide")
st.title("System Status")
st.caption("Runtime capability report for the current Streamlit environment.")


def availability(module: str) -> str:
    return "Available" if importlib.util.find_spec(module) else "Optional dependency missing"

registry = load_contribution_registry()
rows = [
    {"Component": "Python", "Status": platform.python_version()},
    {"Component": "Streamlit", "Status": availability("streamlit")},
    {"Component": "Plotly", "Status": availability("plotly")},
    {"Component": "NetworkX", "Status": availability("networkx")},
    {"Component": "PyYAML", "Status": availability("yaml")},
    {"Component": "FFmpeg", "Status": "Available" if shutil.which("ffmpeg") else "Unavailable in current environment"},
    {"Component": "ROS2", "Status": "Available" if shutil.which("ros2") else "Pending validation"},
    {"Component": "Contribution registry", "Status": f"{len(registry)} entries"},
    {"Component": "Contribution renderers", "Status": f"{len(RENDERERS)} registered"},
]
st.dataframe(rows, hide_index=True, use_container_width=True)

st.subheader("Renderer integrity")
expected = {f"C{i:02d}" for i in range(1, 27)}
registered = set(RENDERERS)
if registered == expected:
    st.success("All C01–C26 renderers are registered.")
else:
    st.error(f"Missing: {sorted(expected - registered)}; unexpected: {sorted(registered - expected)}")

st.subheader("Environment")
st.code(f"Python executable: {sys.executable}\nPlatform: {platform.platform()}", language="text")
st.warning(
    "Availability reports describe this process only. They are not evidence of ROS2, Gazebo, GPU, or physical-robot validation."
)
