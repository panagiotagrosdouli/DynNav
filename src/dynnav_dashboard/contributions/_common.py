"""Shared theming + utility helpers for per-contribution Streamlit demos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS


DARK_BG = COLORS["bg"]
SURFACE = COLORS["surface"]
TEXT = COLORS["text"]
MUTED = COLORS["text_muted"]


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------


def section_header(label: str, sub: Optional[str] = None) -> None:
    """Render a small section header used inside each contribution panel."""
    st.markdown(
        f"<div style='margin-top:0.4rem;'>"
        f"<div style='font-size:0.78rem;letter-spacing:0.12em;color:{MUTED};"
        f"text-transform:uppercase;font-weight:600;'>{label}</div>"
        + (
            f"<div style='font-size:0.85rem;color:{MUTED};margin-top:0.15rem;'>{sub}</div>"
            if sub
            else ""
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def explanation_block(title: str, body: str) -> None:
    """Render the 'short research explanation' block at the top of a demo."""
    st.markdown(
        f"""
        <div style='background:{SURFACE};border-left:3px solid {COLORS["primary"]};
                    border-radius:8px;padding:1rem 1.2rem;margin:0.4rem 0 1rem 0;'>
            <div style='font-size:1.0rem;font-weight:600;color:{TEXT};
                        margin-bottom:0.35rem;'>{title}</div>
            <div style='font-size:0.92rem;color:{TEXT};opacity:0.88;line-height:1.55;'>{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def interpretation_block(body: str) -> None:
    """Render the 'interpretation of results' block at the bottom of a demo."""
    st.markdown(
        f"""
        <div style='background:rgba(167,139,250,0.08);
                    border-left:3px solid {COLORS["accent"]};
                    border-radius:8px;padding:0.9rem 1.1rem;margin:0.6rem 0 0.2rem 0;'>
            <div style='font-size:0.78rem;letter-spacing:0.12em;color:{COLORS["accent"]};
                        text-transform:uppercase;font-weight:600;margin-bottom:0.35rem;'>
                Interpretation
            </div>
            <div style='font-size:0.92rem;color:{TEXT};opacity:0.92;line-height:1.55;'>{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metrics_row(items: Sequence[Tuple[str, str, Optional[str]]]) -> None:
    """Render a row of compact metric cards.

    Each item is (label, value, color). ``color`` may be ``None``.
    """
    if not items:
        return
    cols = st.columns(len(items))
    for col, (label, value, color) in zip(cols, items):
        c = color or COLORS["primary"]
        col.markdown(
            f"""
            <div style='background:{SURFACE};border:1px solid rgba(255,255,255,0.06);
                        border-radius:10px;padding:0.65rem 0.85rem;'>
                <div style='font-size:0.7rem;letter-spacing:0.1em;color:{MUTED};
                            text-transform:uppercase;font-weight:600;'>{label}</div>
                <div style='font-size:1.25rem;font-weight:700;color:{c};margin-top:0.15rem;'>
                    {value}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Plotly theming
# ---------------------------------------------------------------------------


def apply_theme(fig: go.Figure, height: int = 380) -> go.Figure:
    """Apply the dashboard's dark theme to a Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=40, r=20, t=40, b=40),
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(color=TEXT, family="Inter, sans-serif", size=12),
        title=dict(font=dict(size=14, color=TEXT)),
        legend=dict(
            bgcolor="rgba(22,27,34,0.85)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.1)",
            color=TEXT,
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.1)",
            color=TEXT,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Small synthetic-world helpers shared across multiple demos
# ---------------------------------------------------------------------------


def make_grid_with_obstacles(
    size: int,
    n_obstacles: int,
    seed: int,
    obstacle_max_size: int = 4,
) -> np.ndarray:
    """Build a binary occupancy grid with axis-aligned rectangular obstacles."""
    rng = np.random.default_rng(seed)
    grid = np.zeros((size, size), dtype=np.float32)
    placed = 0
    attempts = 0
    while placed < n_obstacles and attempts < n_obstacles * 30:
        attempts += 1
        w = int(rng.integers(2, obstacle_max_size + 1))
        h = int(rng.integers(2, obstacle_max_size + 1))
        x = int(rng.integers(2, size - w - 2))
        y = int(rng.integers(2, size - h - 2))
        # Keep start (2,2) and goal (size-3,size-3) clear
        if x <= 4 and y <= 4:
            continue
        if x + w >= size - 4 and y + h >= size - 4:
            continue
        grid[y:y + h, x:x + w] = 1.0
        placed += 1
    return grid


def astar(
    grid: np.ndarray,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    heuristic_field: Optional[np.ndarray] = None,
    risk_weight: float = 0.0,
    risk_field: Optional[np.ndarray] = None,
) -> Dict:
    """Generic 8-connected A* used by several demos.

    Parameters
    ----------
    grid : np.ndarray
        Binary occupancy grid (1.0 = obstacle).
    start, goal : (x, y) tuples
        Indexed so that ``grid[y, x]`` is the cell.
    heuristic_field : np.ndarray, optional
        Additive per-cell bias on top of the standard octile heuristic.
        Used by C01 to mimic a learned heuristic.
    risk_weight, risk_field : optional
        If both provided, each step pays ``risk_weight * risk_field[y, x]``.
    """
    import heapq

    H, W = grid.shape
    sx, sy = start
    gx, gy = goal

    def h(x: int, y: int) -> float:
        dx, dy = abs(x - gx), abs(y - gy)
        base = max(dx, dy) + (np.sqrt(2) - 1) * min(dx, dy)
        bias = float(heuristic_field[y, x]) if heuristic_field is not None else 0.0
        return base + bias

    open_heap: List[Tuple[float, int, Tuple[int, int]]] = []
    heapq.heappush(open_heap, (h(sx, sy), 0, (sx, sy)))
    g_cost: Dict[Tuple[int, int], float] = {(sx, sy): 0.0}
    came: Dict[Tuple[int, int], Tuple[int, int]] = {}
    expansions = 0
    counter = 1
    closed = set()

    while open_heap:
        _, _, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        expansions += 1
        if cur == (gx, gy):
            # Reconstruct
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            path.reverse()
            return {
                "path": path,
                "expansions": expansions,
                "cost": g_cost[(gx, gy)],
                "success": True,
            }
        cx, cy = cur
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < W and 0 <= ny < H):
                    continue
                if grid[ny, nx] > 0.5:
                    continue
                step = np.sqrt(2) if dx and dy else 1.0
                if risk_field is not None and risk_weight > 0:
                    step += risk_weight * float(risk_field[ny, nx])
                ng = g_cost[cur] + step
                if ng < g_cost.get((nx, ny), float("inf")):
                    g_cost[(nx, ny)] = ng
                    came[(nx, ny)] = cur
                    f = ng + h(nx, ny)
                    heapq.heappush(open_heap, (f, counter, (nx, ny)))
                    counter += 1
    return {"path": [], "expansions": expansions, "cost": float("inf"), "success": False}


def grid_heatmap_trace(grid: np.ndarray, name: str = "occupancy") -> go.Heatmap:
    """Return a Plotly Heatmap trace for a binary occupancy grid."""
    return go.Heatmap(
        z=grid,
        colorscale=[
            [0.0, "rgba(14,17,23,0)"],
            [0.5, "rgba(150,150,160,0.35)"],
            [1.0, "rgba(180,180,190,0.95)"],
        ],
        showscale=False,
        name=name,
        hoverinfo="skip",
    )


def path_trace(
    path: Iterable[Tuple[int, int]],
    color: str,
    name: str,
    width: float = 3.0,
    dash: Optional[str] = None,
) -> go.Scatter:
    """Return a Plotly Scatter trace for a path."""
    pts = list(path)
    if not pts:
        return go.Scatter(x=[], y=[], mode="lines", name=name)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        name=name,
        line=dict(color=color, width=width, dash=dash or "solid"),
        hoverinfo="name",
    )


def point_trace(
    x: float,
    y: float,
    color: str,
    name: str,
    symbol: str = "circle",
    size: int = 14,
) -> go.Scatter:
    """Return a Plotly Scatter trace for a single labelled point."""
    return go.Scatter(
        x=[x],
        y=[y],
        mode="markers",
        name=name,
        marker=dict(
            color=color,
            size=size,
            symbol=symbol,
            line=dict(color="#0E1117", width=1.5),
        ),
    )


def square_axes(fig: go.Figure, size: int) -> go.Figure:
    """Lock aspect ratio for grid plots."""
    fig.update_xaxes(range=[-0.5, size - 0.5], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(range=[-0.5, size - 0.5])
    return fig
