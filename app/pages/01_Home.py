from __future__ import annotations

import streamlit as st

from dynnav_dashboard.registry import load_contribution_registry

st.set_page_config(page_title="DynNav Robotics Lab", page_icon="🧭", layout="wide")

st.title("DynNav Interactive Robotics Lab")
st.caption(
    "Interactive research software designed to the usability, reproducibility, and scientific communication "
    "standards expected of leading robotics laboratories."
)
st.info(
    "Synthetic interactive research environment. Results shown here do not establish physical-robot safety, "
    "ROS2 validation, deployment readiness, or formal guarantees."
)

st.markdown(
    """
    DynNav studies how a mobile robot can plan and replan while its map is incomplete, obstacles move, uncertainty
    changes, and mission-level safety constraints remain active. Use the laboratory pages to run the closed-loop
    robot, compare planning behavior, and interact with the contribution-specific research demonstrations.
    """
)

c1, c2, c3 = st.columns(3)
c1.metric("Interactive contributions", "26")
c2.metric("Closed-loop planners", "2")
c3.metric("Evidence type", "Synthetic")

st.subheader("Start an experiment")
left, middle, right = st.columns(3)
with left:
    st.markdown("### Drive the robot")
    st.write("Run the closed-loop navigation simulation and replay replanning events.")
    st.page_link("pages/02_Robot_Lab.py", label="Open Robot Lab", icon="▶️")
with middle:
    st.markdown("### Explore contributions")
    st.write("Search C01–C26 and change the parameters of each research demonstration.")
    st.page_link("pages/09_Contribution_Explorer.py", label="Open Contribution Explorer", icon="🔬")
with right:
    st.markdown("### Inspect the environment")
    st.write("Review package, renderer, dependency, and runtime availability.")
    st.page_link("pages/13_System_Status.py", label="Open System Status", icon="🧪")

st.subheader("Closed-loop architecture")
st.code(
    "Observation → occupancy belief → uncertainty → risk → candidate planning → route monitoring → "
    "supervisor action → robot motion → metrics and explanations",
    language="text",
)

registry = load_contribution_registry()
category_counts: dict[str, int] = {}
for item in registry:
    category_counts[item.category] = category_counts.get(item.category, 0) + 1

st.subheader("Research contribution catalogue")
st.dataframe(
    [{"Category": category, "Contributions": count} for category, count in sorted(category_counts.items())],
    hide_index=True,
    use_container_width=True,
)
