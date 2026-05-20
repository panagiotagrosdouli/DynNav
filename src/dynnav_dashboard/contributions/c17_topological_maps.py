"""C17 — Topological Maps: semantic graph navigation between rooms."""

from __future__ import annotations

import numpy as np
import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS
from ._common import (
    apply_theme,
    explanation_block,
    interpretation_block,
    metrics_row,
    section_header,
)


def _build_floor_plan(seed: int):
    """Synthetic floor plan of rooms as a topological graph."""
    rng = np.random.default_rng(seed)
    rooms = [
        ("Entrance",    (0, 2), "lobby"),
        ("Corridor 1",  (2, 2), "corridor"),
        ("Living Room", (4, 4), "social"),
        ("Kitchen",     (5, 3), "service"),
        ("Office",      (4, 1), "work"),
        ("Bedroom 1",   (6, 5), "private"),
        ("Bedroom 2",   (7, 4), "private"),
        ("Bathroom",    (6, 2), "service"),
        ("Corridor 2",  (5, 2), "corridor"),
        ("Garage",      (1, 0), "service"),
        ("Storage",     (3, 5), "service"),
    ]
    G = nx.Graph()
    for name, pos, cat in rooms:
        G.add_node(name, pos=pos, category=cat)
    # Edges = doorways. Slightly noisy weights as walking-time costs.
    doorways = [
        ("Entrance", "Corridor 1"),
        ("Corridor 1", "Office"),
        ("Corridor 1", "Living Room"),
        ("Corridor 1", "Garage"),
        ("Living Room", "Kitchen"),
        ("Living Room", "Storage"),
        ("Kitchen", "Corridor 2"),
        ("Corridor 2", "Bathroom"),
        ("Corridor 2", "Bedroom 1"),
        ("Bedroom 1", "Bedroom 2"),
    ]
    for u, v in doorways:
        pu = np.array(G.nodes[u]["pos"]); pv = np.array(G.nodes[v]["pos"])
        w = float(np.linalg.norm(pu - pv) + rng.uniform(-0.1, 0.1))
        G.add_edge(u, v, weight=max(w, 0.3))
    return G


_CAT_COLORS = {
    "lobby": COLORS["primary"],
    "corridor": COLORS["text_muted"],
    "social": COLORS["secondary"],
    "service": COLORS["highlight"],
    "work": COLORS["accent"],
    "private": COLORS["danger"],
}


def render(st_ctx=st) -> None:
    explanation_block(
        "C17 — Topological Maps: Semantic Graph Navigation",
        "At large scales metric grids become wasteful. DynNav builds a "
        "topological map — rooms as nodes, doorways as edges — and plans "
        "at this semantic level. Edge weights are average walking-time "
        "estimates; node attributes carry the room category so a "
        "high-level LLM planner can refer to <i>'go to the kitchen'</i> "
        "and the topological layer handles the rest.",
    )

    section_header("Interactive controls")
    G = _build_floor_plan(seed=2)
    nodes = list(G.nodes())
    c1, c2 = st.columns(2)
    src = c1.selectbox("Start room", nodes, index=nodes.index("Entrance"), key="c17_s")
    dst = c2.selectbox("Goal room", nodes, index=nodes.index("Bedroom 2"), key="c17_g")

    try:
        path = nx.shortest_path(G, src, dst, weight="weight")
        cost = nx.shortest_path_length(G, src, dst, weight="weight")
    except nx.NetworkXNoPath:
        path, cost = [], float("inf")

    section_header("Floor-plan graph and planned route")
    fig = go.Figure()
    # Edges
    for u, v, data in G.edges(data=True):
        x0, y0 = G.nodes[u]["pos"]; x1, y1 = G.nodes[v]["pos"]
        in_path = (
            path
            and (u, v) in zip(path, path[1:])
            or path and (v, u) in zip(path, path[1:])
        )
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(
                color=COLORS["success"] if in_path else "rgba(110,118,129,0.45)",
                width=4 if in_path else 1.5,
                dash="solid" if in_path else "dot",
            ),
            hoverinfo="text", hovertext=f"{u} ↔ {v} (w={data['weight']:.2f})",
            showlegend=False,
        ))
    # Nodes
    nx_x, nx_y, nx_text, nx_color = [], [], [], []
    for n in G.nodes():
        x, y = G.nodes[n]["pos"]
        nx_x.append(x); nx_y.append(y)
        cat = G.nodes[n]["category"]
        nx_text.append(f"{n}<br>{cat}")
        nx_color.append(_CAT_COLORS.get(cat, COLORS["primary"]))
    fig.add_trace(go.Scatter(
        x=nx_x, y=nx_y, mode="markers+text",
        marker=dict(color=nx_color, size=42,
                     line=dict(color="#0E1117", width=2)),
        text=[n for n in G.nodes()], textposition="middle center",
        textfont=dict(size=10, color=COLORS["text"]),
        hovertext=nx_text, hoverinfo="text", showlegend=False,
    ))
    # Highlight src and dst
    sx, sy = G.nodes[src]["pos"]
    gx, gy = G.nodes[dst]["pos"]
    fig.add_trace(go.Scatter(
        x=[sx, gx], y=[sy, gy], mode="markers",
        marker=dict(color=[COLORS["primary"], COLORS["success"]], size=58,
                     symbol=["square", "star"], line=dict(color="#0E1117", width=2),
                     opacity=0.45),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=460), use_container_width=True)

    metrics_row([
        ("Rooms (nodes)", f"{G.number_of_nodes()}", COLORS["primary"]),
        ("Doorways (edges)", f"{G.number_of_edges()}", COLORS["primary"]),
        ("Hops", f"{max(len(path) - 1, 0)}", COLORS["secondary"]),
        ("Total walking cost",
         "—" if not path else f"{cost:.2f}", COLORS["success"]),
    ])

    if path:
        st.markdown(
            "**Route:** " + " → ".join(f"`{p}`" for p in path),
            unsafe_allow_html=False,
        )

    interpretation_block(
        "Planning on a topological map costs <i>O(V log V)</i> regardless "
        "of the floor's metric size — orders of magnitude cheaper than grid "
        "A*. DynNav combines the two: topological routing chooses a sequence "
        "of rooms, then a local metric planner handles intra-room motion. "
        "Node categories also let the LLM planner translate user intent "
        "(<i>'go to a quiet workspace'</i>) into a valid destination."
    )
