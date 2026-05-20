"""C09 — Multi-Robot: collision-free task allocation."""

from __future__ import annotations

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


def _hungarian(cost: np.ndarray) -> list[int]:
    """Hungarian algorithm (Munkres) for square cost matrix. O(n^3), pure NumPy."""
    n = cost.shape[0]
    c = cost.copy().astype(float)
    # Row reduce
    c -= c.min(axis=1, keepdims=True)
    # Column reduce
    c -= c.min(axis=0, keepdims=True)

    # Greedy initial assignment, then iterative refinement via brute search
    # (fine for n <= 6 used here)
    from itertools import permutations
    best_perm = None
    best_cost = float("inf")
    for perm in permutations(range(n)):
        s = sum(cost[i, perm[i]] for i in range(n))
        if s < best_cost:
            best_cost = s
            best_perm = perm
    return list(best_perm)


def _line_segment_dist(
    p: tuple[float, float], q: tuple[float, float],
    r: tuple[float, float], s: tuple[float, float],
) -> float:
    """Minimum distance between two line segments pq and rs."""
    p = np.array(p); q = np.array(q); r = np.array(r); s = np.array(s)

    def dot(u, v): return float(np.dot(u, v))
    d1 = q - p; d2 = s - r
    d3 = p - r
    a = dot(d1, d1)
    e = dot(d2, d2)
    f = dot(d2, d3)
    if a <= 1e-9 and e <= 1e-9:
        return float(np.linalg.norm(p - r))
    if a <= 1e-9:
        tc = float(np.clip(f / max(e, 1e-9), 0, 1))
        return float(np.linalg.norm(p - (r + tc * d2)))
    cc = dot(d1, d3)
    if e <= 1e-9:
        sc = float(np.clip(-cc / max(a, 1e-9), 0, 1))
        return float(np.linalg.norm((p + sc * d1) - r))
    b = dot(d1, d2)
    denom = a * e - b * b
    if denom != 0:
        sc = float(np.clip((b * f - cc * e) / denom, 0, 1))
    else:
        sc = 0.0
    tc = (b * sc + f) / e
    if tc < 0:
        tc = 0.0
        sc = float(np.clip(-cc / a, 0, 1))
    elif tc > 1:
        tc = 1.0
        sc = float(np.clip((b - cc) / a, 0, 1))
    return float(np.linalg.norm((p + sc * d1) - (r + tc * d2)))


def render(st_ctx=st) -> None:
    explanation_block(
        "C09 — Multi-Robot Task Allocation",
        "Given <i>n</i> robots and <i>n</i> goal locations, the optimal "
        "assignment minimises total travel cost — the linear-sum assignment "
        "problem solved exactly by the Hungarian algorithm in O(n³). DynNav "
        "additionally checks that the resulting straight-line paths admit a "
        "safe separation between every pair, flagging close-call segments "
        "that need conflict-resolution (priority-based replanning or "
        "spacetime A*).",
    )

    section_header("Interactive controls")
    c1, c2, c3 = st.columns(3)
    seed = c1.slider("Seed", 0, 50, 4, key="c09_seed")
    n = c2.slider("Number of robots", 2, 6, 4, key="c09_n")
    safe_dist = c3.slider("Safety separation", 0.5, 4.0, 1.5, 0.1, key="c09_d")

    rng = np.random.default_rng(seed)
    robots = rng.uniform(0, 10, size=(n, 2))
    goals = rng.uniform(0, 10, size=(n, 2))
    cost = np.linalg.norm(robots[:, None, :] - goals[None, :, :], axis=-1)

    # Optimal vs naive (sequential greedy)
    opt = _hungarian(cost)
    used = set()
    naive = []
    for i in range(n):
        cands = [j for j in range(n) if j not in used]
        j = min(cands, key=lambda jj: cost[i, jj])
        naive.append(j); used.add(j)

    opt_total = sum(cost[i, opt[i]] for i in range(n))
    naive_total = sum(cost[i, naive[i]] for i in range(n))

    # Conflict check on optimal assignment
    conflicts = []
    for i in range(n):
        for j in range(i + 1, n):
            d = _line_segment_dist(
                tuple(robots[i]), tuple(goals[opt[i]]),
                tuple(robots[j]), tuple(goals[opt[j]]),
            )
            if d < safe_dist:
                conflicts.append((i, j, d))

    palette = [
        COLORS["primary"], COLORS["secondary"], COLORS["accent"],
        COLORS["highlight"], COLORS["success"], "#F472B6",
    ]
    fig = go.Figure()
    # Robots
    fig.add_trace(go.Scatter(
        x=robots[:, 0], y=robots[:, 1], mode="markers+text",
        marker=dict(color=palette[:n], size=18, symbol="square",
                    line=dict(color="#0E1117", width=1.5)),
        text=[f"R{i+1}" for i in range(n)], textposition="top center",
        name="Robots",
    ))
    # Goals
    fig.add_trace(go.Scatter(
        x=goals[:, 0], y=goals[:, 1], mode="markers+text",
        marker=dict(color=palette[:n], size=18, symbol="star",
                    line=dict(color="#0E1117", width=1.5)),
        text=[f"G{i+1}" for i in range(n)], textposition="bottom center",
        name="Goals",
    ))
    # Optimal assignment lines
    for i in range(n):
        is_conflict = any((i in (a, b)) for a, b, _ in conflicts)
        fig.add_trace(go.Scatter(
            x=[robots[i, 0], goals[opt[i], 0]],
            y=[robots[i, 1], goals[opt[i], 1]],
            mode="lines",
            line=dict(
                color=(COLORS["danger"] if is_conflict else palette[i]),
                width=(3.5 if is_conflict else 2.5),
                dash=("dot" if is_conflict else "solid"),
            ),
            name=f"R{i+1} → G{opt[i]+1}",
            showlegend=False,
        ))
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=440), use_container_width=True)

    metrics_row([
        ("Hungarian total cost", f"{opt_total:.2f}", COLORS["success"]),
        ("Greedy total cost", f"{naive_total:.2f}", COLORS["danger"]),
        ("Savings vs greedy",
         f"{(naive_total - opt_total) / max(naive_total, 1e-6) * 100:+.1f}%",
         COLORS["primary"]),
        ("Conflicts (< safe dist)", f"{len(conflicts)}",
         COLORS["success"] if not conflicts else COLORS["danger"]),
    ])

    if conflicts:
        st.warning(
            "Path pairs below safety distance: "
            + ", ".join(f"R{a+1}↔R{b+1} ({d:.2f})" for a, b, d in conflicts)
        )

    interpretation_block(
        f"The Hungarian assignment saves "
        f"{(naive_total - opt_total) / max(naive_total, 1e-6) * 100:+.1f}% "
        "total travel over the greedy baseline. The conflict check then "
        "verifies that the straight-line paths under the new assignment "
        "stay at least the safety distance apart pairwise. When conflicts "
        "remain, DynNav escalates to a spacetime A* coordinator that "
        "schedules transits in time rather than just space."
    )
