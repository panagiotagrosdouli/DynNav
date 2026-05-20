"""C19 — LLM Planner: natural language mission parsed into waypoints."""

from __future__ import annotations

import re
from typing import List, Tuple

import numpy as np
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


# Synthetic "semantic map" of named locations on a 10×10 area
LOCATIONS: dict[str, tuple[float, float]] = {
    "base": (1.0, 1.0),
    "entrance": (1.5, 2.0),
    "lobby": (2.5, 2.5),
    "corridor": (4.0, 3.0),
    "kitchen": (6.0, 5.0),
    "office": (5.5, 7.0),
    "lab": (7.5, 6.5),
    "warehouse": (8.5, 2.0),
    "loading_bay": (9.0, 1.0),
    "battery_dock": (1.5, 9.0),
    "server_room": (3.0, 8.0),
    "meeting_room": (4.5, 6.0),
    "patient_room_a": (7.0, 8.5),
    "patient_room_b": (8.5, 7.5),
    "exit": (9.5, 9.5),
}

# Intent verbs the planner understands
VERBS = {
    "go": "visit", "navigate": "visit", "move": "visit", "head": "visit",
    "visit": "visit", "stop": "visit",
    "pick": "pickup", "grab": "pickup", "collect": "pickup", "fetch": "pickup",
    "drop": "dropoff", "deliver": "dropoff", "deposit": "dropoff",
    "patrol": "patrol", "inspect": "inspect", "scan": "inspect",
    "return": "return", "dock": "return", "recharge": "return",
}


def _parse_mission(text: str) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Very small rule-based 'LLM' parser → list of (action, location) steps.

    Returns the parsed plan and a list of warnings for unrecognised tokens.
    """
    if not text.strip():
        return [], []
    # Normalise
    txt = text.lower().replace(",", " , ")
    # Split on sentence/clause boundaries
    clauses = re.split(r"\s*(?:then|;|\.|,|->|→|and then|, then)\s*", txt)
    plan: List[Tuple[str, str]] = []
    warnings: List[str] = []
    location_names = list(LOCATIONS.keys())

    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        words = re.findall(r"[a-zA-Z_]+", clause)
        if not words:
            continue
        # find verb
        action = None
        for w in words:
            if w in VERBS:
                action = VERBS[w]
                break
        if action is None:
            action = "visit"  # default
        # find first matching location (greedy underscore-merged match)
        joined = "_".join(words)
        loc = None
        for ln in sorted(location_names, key=len, reverse=True):
            if ln in joined:
                loc = ln
                break
        if loc is None:
            warnings.append(f"could not find a known location in: '{clause}'")
            continue
        plan.append((action, loc))
    return plan, warnings


def render(st_ctx=st) -> None:
    explanation_block(
        "C19 — LLM Planner: Natural Language Mission to Waypoints",
        "DynNav exposes an LLM-driven planning layer so an operator can "
        "issue missions in plain language. The LLM parses the utterance "
        "into a typed plan — a sequence of (action, location) tuples — "
        "and the topological layer compiles it into a metric path. This "
        "demo uses a deterministic rule-based parser to stand in for the "
        "LLM, but the contract with downstream layers is identical: "
        "structured intent in, executable plan out.",
    )

    section_header("Interactive controls")
    examples = {
        "Multi-stop delivery": (
            "Go to the warehouse, pick up the package, "
            "then deliver to patient_room_a, then return to battery_dock."
        ),
        "Inspection round": (
            "Patrol the corridor, inspect the server_room, "
            "then visit the lab and return to base."
        ),
        "Simple errand": "Navigate to the kitchen then go to the office.",
        "Free text (edit below)": "",
    }
    c1, c2 = st.columns([1.0, 2.0])
    choice = c1.selectbox(
        "Example missions", list(examples.keys()), index=0, key="c19_ex",
    )
    default_text = examples[choice] or "Go to kitchen then return to base."
    text = c2.text_area(
        "Mission (natural language)",
        value=default_text, height=100, key="c19_text",
    )

    plan, warnings = _parse_mission(text)

    section_header("Parsed plan")
    if plan:
        rows = "".join(
            f"<tr><td style='padding:4px 12px;color:{COLORS['text_muted']}'>"
            f"{i+1}</td>"
            f"<td style='padding:4px 12px;color:{COLORS['secondary']};"
            f"font-weight:600'>{a}</td>"
            f"<td style='padding:4px 12px;color:{COLORS['text']}'>{loc}</td></tr>"
            for i, (a, loc) in enumerate(plan)
        )
        st.markdown(
            f"<table style='border-collapse:collapse;font-size:0.9rem'>"
            f"<thead><tr>"
            f"<th style='padding:4px 12px;color:{COLORS['text_muted']};"
            f"text-align:left'>#</th>"
            f"<th style='padding:4px 12px;color:{COLORS['text_muted']};"
            f"text-align:left'>Action</th>"
            f"<th style='padding:4px 12px;color:{COLORS['text_muted']};"
            f"text-align:left'>Location</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>",
            unsafe_allow_html=True,
        )
    else:
        st.warning("No actionable steps were parsed.")
    for w in warnings:
        st.info(w)

    # Compile to metric waypoints
    waypoints = [LOCATIONS[loc] for _action, loc in plan]
    full = [LOCATIONS["base"]] + waypoints if waypoints else [LOCATIONS["base"]]
    xs = [p[0] for p in full]
    ys = [p[1] for p in full]
    total_dist = float(
        sum(
            np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i])
            for i in range(len(xs) - 1)
        )
    )

    section_header("Compiled metric path")
    fig = go.Figure()
    # All landmarks
    lx = [p[0] for p in LOCATIONS.values()]
    ly = [p[1] for p in LOCATIONS.values()]
    ln = list(LOCATIONS.keys())
    fig.add_trace(go.Scatter(
        x=lx, y=ly, mode="markers+text",
        marker=dict(color=COLORS["text_muted"], size=10,
                    line=dict(color="#0E1117", width=1)),
        text=ln, textposition="top center",
        textfont=dict(size=10, color=COLORS["text_muted"]),
        name="Known locations", hoverinfo="text",
    ))
    if len(full) >= 2:
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers",
            line=dict(color=COLORS["secondary"], width=3),
            marker=dict(color=COLORS["secondary"], size=12,
                        line=dict(color="#0E1117", width=1.5)),
            name="Planned path",
        ))
    fig.add_trace(go.Scatter(
        x=[LOCATIONS["base"][0]], y=[LOCATIONS["base"][1]],
        mode="markers", marker=dict(color=COLORS["primary"], size=18,
                                     symbol="square",
                                     line=dict(color="#0E1117", width=1.5)),
        name="Start (base)",
    ))
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=440), use_container_width=True)

    metrics_row([
        ("Parsed steps", f"{len(plan)}", COLORS["secondary"]),
        ("Unique waypoints",
         f"{len({loc for _, loc in plan})}", COLORS["primary"]),
        ("Total path length", f"{total_dist:.2f} units", COLORS["success"]),
        ("Parse warnings", f"{len(warnings)}",
         COLORS["text_muted"] if not warnings else COLORS["highlight"]),
    ])

    interpretation_block(
        f"The natural-language mission compiled into {len(plan)} discrete "
        f"steps spanning {total_dist:.2f} units of travel. A real LLM "
        "planner adds two capabilities this demo skips: (1) resolving "
        "ambiguous references (<i>'the closest meeting room'</i>) using "
        "the topological map and (2) inserting implicit preconditions "
        "(<i>'pick up'</i> requires being <i>at</i> the object). DynNav "
        "wraps the LLM output in a safety check before commit — any plan "
        "that would violate returnability or energy limits is rejected "
        "before execution begins."
    )
