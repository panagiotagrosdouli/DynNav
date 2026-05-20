"""C04 — Returnability: dead-end detection and return-safe planning."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS
from ._common import (
    apply_theme,
    astar,
    explanation_block,
    grid_heatmap_trace,
    interpretation_block,
    make_grid_with_obstacles,
    metrics_row,
    path_trace,
    point_trace,
    section_header,
    square_axes,
)


def _carve_corridor(grid: np.ndarray, seed: int) -> np.ndarray:
    """Carve a dead-end corridor so we can see returnability in action."""
    g = grid.copy()
    H, W = g.shape
    rng = np.random.default_rng(seed + 17)
    # Build a U-shaped trap toward the lower-right.
    cy = H - 8
    cx = W - 10
    # Open a corridor
    g[cy:cy + 2, cx - 6:cx + 1] = 0.0
    g[cy - 5:cy + 2, cx - 1:cx + 1] = 0.0
    # Cap the far end (dead-end)
    g[cy - 5:cy - 3, cx - 6:cx + 1] = 1.0
    return g


def _ensure_returnable(
    grid: np.ndarray,
    start,
    goal,
    risk_threshold: float,
    occupancy_risk: np.ndarray,
) -> dict:
    """Plan a 'returnable' path: the goal must also have a feasible route back.

    We test returnability by replanning from goal to start under the same map
    and rejecting the candidate goal if no return path exists or its risk
    exceeds the threshold.
    """
    out_path = astar(grid, start, goal)
    if not out_path["success"]:
        return {"path": [], "return": [], "returnable": False, "reason": "no outbound path"}
    back_path = astar(grid, goal, start)
    if not back_path["success"]:
        return {
            "path": out_path["path"],
            "return": [],
            "returnable": False,
            "reason": "no return path (dead-end)",
        }
    return_risk = float(np.mean([occupancy_risk[y, x] for x, y in back_path["path"]]))
    if return_risk > risk_threshold:
        return {
            "path": out_path["path"],
            "return": back_path["path"],
            "returnable": False,
            "reason": f"return risk {return_risk:.2f} > threshold {risk_threshold:.2f}",
            "return_risk": return_risk,
        }
    return {
        "path": out_path["path"],
        "return": back_path["path"],
        "returnable": True,
        "reason": "OK",
        "return_risk": return_risk,
    }


def render(st_ctx=st) -> None:
    explanation_block(
        "C04 — Returnability: Mission-Safe Path Planning",
        "A path is 'returnable' if, in addition to reaching the goal, the "
        "robot can also get back — under the same map, the same battery "
        "budget and the same risk constraints. Returnability checks are "
        "critical for exploration, inspection and emergency recall: a "
        "shorter outbound path that leads into a dead-end or one-way "
        "corridor is unacceptable. DynNav rejects such goals or flags "
        "them as advisory.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4 = st.columns(4)
    seed = c1.slider("Seed", 0, 50, 5, key="c04_seed")
    size = c2.slider("Grid size", 25, 50, 35, key="c04_size")
    n_obs = c3.slider("Obstacles", 5, 20, 10, key="c04_obs")
    th = c4.slider("Return risk threshold", 0.1, 1.0, 0.6, 0.05, key="c04_th")

    base = make_grid_with_obstacles(size, n_obs, seed)
    grid = _carve_corridor(base, seed)
    start = (2, 2)
    goal_a = (size - 5, size - 6)        # in the dead-end trap
    goal_b = (size - 3, 3)                # open area, returnable
    grid[start[1], start[0]] = 0
    grid[goal_a[1], goal_a[0]] = 0
    grid[goal_b[1], goal_b[0]] = 0

    # Light synthetic risk field (clutter proximity)
    risk = grid.copy() * 0.0
    pad = 2
    for dy in range(-pad, pad + 1):
        for dx in range(-pad, pad + 1):
            r = np.hypot(dx, dy)
            if r > pad:
                continue
            shifted = np.roll(np.roll(grid, dy, axis=0), dx, axis=1)
            risk = np.maximum(risk, shifted * (1.0 - r / (pad + 1)))
    risk = risk * 0.8

    ra = _ensure_returnable(grid, start, goal_a, th, risk)
    rb = _ensure_returnable(grid, start, goal_b, th, risk)

    section_header("Map: dead-end goal vs returnable goal")
    fig = go.Figure()
    fig.add_trace(grid_heatmap_trace(grid))
    if ra["path"]:
        fig.add_trace(path_trace(
            ra["path"], COLORS["danger"],
            "Outbound to trap goal", width=3.0,
        ))
    if ra.get("return"):
        fig.add_trace(path_trace(
            ra["return"], COLORS["highlight"],
            "Return from trap goal", width=2.5, dash="dot",
        ))
    if rb["path"]:
        fig.add_trace(path_trace(
            rb["path"], COLORS["primary"],
            "Outbound to safe goal", width=3.0,
        ))
    if rb.get("return"):
        fig.add_trace(path_trace(
            rb["return"], COLORS["secondary"],
            "Return from safe goal", width=2.5, dash="dot",
        ))
    fig.add_trace(point_trace(*start, COLORS["primary"], "Start"))
    fig.add_trace(point_trace(*goal_a, COLORS["danger"], "Goal A (in trap)", symbol="x", size=18))
    fig.add_trace(point_trace(*goal_b, COLORS["success"], "Goal B (safe)", symbol="star", size=18))
    square_axes(fig, size)
    st.plotly_chart(apply_theme(fig, height=460), use_container_width=True)

    section_header("Returnability verdicts")
    c1, c2 = st.columns(2)
    with c1:
        verdict_a = "RETURNABLE" if ra["returnable"] else "NOT RETURNABLE"
        color_a = COLORS["success"] if ra["returnable"] else COLORS["danger"]
        metrics_row([
            ("Goal A — verdict", verdict_a, color_a),
            ("Reason", ra["reason"], COLORS["text_muted"]),
        ])
    with c2:
        verdict_b = "RETURNABLE" if rb["returnable"] else "NOT RETURNABLE"
        color_b = COLORS["success"] if rb["returnable"] else COLORS["danger"]
        metrics_row([
            ("Goal B — verdict", verdict_b, color_b),
            ("Reason", rb["reason"], COLORS["text_muted"]),
        ])

    interpretation_block(
        "Goal A sits in a U-shaped corridor crafted to look attractive on "
        "the outbound leg but to expose high return risk (or no return path "
        "at all under tight thresholds). DynNav's returnability check uses "
        "the same planner with start and goal swapped — a cheap test that "
        "catches one-way commitments before the robot is stranded. Adjust "
        "the risk threshold to see how a conservative supervisor would "
        "reject otherwise-feasible goals."
    )
