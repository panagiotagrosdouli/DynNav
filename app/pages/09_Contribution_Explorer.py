from __future__ import annotations

import streamlit as st

from dynnav_dashboard.contributions import RENDERERS
from dynnav_dashboard.registry import load_contribution_registry

st.set_page_config(page_title="Contribution Explorer", page_icon="🔬", layout="wide")
st.title("Contribution Explorer")
st.caption("Search, filter, and interact with every registered DynNav research contribution.")
st.info(
    "Each page displays its maturity from the central registry. Interactive synthetic behavior does not imply "
    "hardware, ROS2, or formal safety validation."
)

registry = load_contribution_registry()
categories = sorted({item.category for item in registry})
maturities = sorted({item.maturity for item in registry})

with st.sidebar:
    query = st.text_input("Search", placeholder="risk, mapping, multi-robot...")
    category = st.selectbox("Category", ["All"] + categories)
    maturity = st.selectbox("Maturity", ["All"] + maturities)

filtered = [
    item
    for item in registry
    if (category == "All" or item.category == category)
    and (maturity == "All" or item.maturity == maturity)
    and (not query or query.lower() in f"{item.id} {item.title} {item.summary} {item.category}".lower())
]

if not filtered:
    st.warning("No contributions match the current filters.")
    st.stop()

labels = {f"{item.id} — {item.title}": item for item in filtered}
selected_label = st.selectbox("Contribution", list(labels))
selected = labels[selected_label]

m1, m2, m3 = st.columns(3)
m1.metric("Contribution", selected.id)
m2.metric("Category", selected.category)
m3.metric("Maturity", selected.maturity)
st.markdown(f"**Research summary:** {selected.summary}")

renderer = RENDERERS.get(selected.id)
if renderer is None:
    st.error(f"No renderer is registered for {selected.id}.")
    st.stop()

with st.container(border=True):
    renderer(st)
