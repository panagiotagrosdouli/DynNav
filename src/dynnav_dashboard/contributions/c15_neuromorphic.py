"""C15 — Neuromorphic: event-camera spike raster and fast obstacle detection."""

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


def _generate_events(
    n_pixels: int, duration_ms: int, n_obstacles: int,
    bg_rate: float, sig_rate: float, seed: int,
):
    """Synthetic event-camera stream.

    Each event = (t_ms, pixel_y, polarity). Background events are spatially
    uniform; obstacles produce bursts of correlated events along trajectories.
    """
    rng = np.random.default_rng(seed)
    # Background events (Poisson)
    n_bg = rng.poisson(bg_rate * duration_ms)
    bg_t = rng.uniform(0, duration_ms, size=n_bg)
    bg_y = rng.integers(0, n_pixels, size=n_bg)
    bg_p = rng.choice([-1, 1], size=n_bg)

    # Obstacle events: each obstacle is a moving 'line' of pixels
    sig_t, sig_y, sig_p = [], [], []
    obstacles = []
    for _ in range(n_obstacles):
        t_start = rng.uniform(0, duration_ms * 0.6)
        t_end = min(duration_ms, t_start + rng.uniform(15, 40))
        y_start = float(rng.uniform(5, n_pixels - 5))
        v = rng.uniform(-1.5, 1.5)
        n_evt = rng.poisson(sig_rate * (t_end - t_start))
        ts = rng.uniform(t_start, t_end, size=n_evt)
        ys = np.clip(y_start + v * (ts - t_start) + rng.normal(0, 0.8, size=n_evt),
                       0, n_pixels - 1)
        ps = rng.choice([-1, 1], size=n_evt)
        sig_t.append(ts); sig_y.append(ys); sig_p.append(ps)
        obstacles.append({"t_start": t_start, "t_end": t_end,
                            "y_start": y_start, "v": v, "n_evt": n_evt})

    if sig_t:
        sig_t = np.concatenate(sig_t)
        sig_y = np.concatenate(sig_y)
        sig_p = np.concatenate(sig_p)
    else:
        sig_t = np.array([]); sig_y = np.array([]); sig_p = np.array([])

    return (bg_t, bg_y, bg_p, sig_t, sig_y, sig_p, obstacles)


def _detect(
    events_t, events_y, n_pixels, duration_ms, bin_ms, threshold,
):
    """Per-bin event count; bins above threshold flag an obstacle."""
    n_bins = max(1, int(duration_ms / bin_ms))
    counts = np.zeros(n_bins, dtype=int)
    for t in events_t:
        b = min(int(t / bin_ms), n_bins - 1)
        counts[b] += 1
    fired = counts > threshold
    return counts, fired


def render(st_ctx=st) -> None:
    explanation_block(
        "C15 — Neuromorphic Event Cameras: Microsecond Obstacle Detection",
        "Event cameras emit a sparse asynchronous stream of pixel-level "
        "brightness changes — typical latencies are sub-millisecond and "
        "the dynamic range exceeds 120 dB. DynNav uses event-rate spikes "
        "in temporal bins as a fast obstacle pre-flag, far below the latency "
        "of a frame-based detector. When a bin's event count exceeds an "
        "adaptive threshold, the safety supervisor can pre-empt the "
        "planner before a conventional perception pipeline has finished "
        "processing.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 9, key="c15_seed")
    duration = c2.slider("Duration (ms)", 50, 400, 200, 10, key="c15_d")
    n_obs = c3.slider("Number of objects", 0, 6, 3, key="c15_no")
    bin_ms = c4.slider("Detection bin (ms)", 1, 20, 5, key="c15_b")
    thr = c5.slider("Spike threshold", 5, 200, 60, key="c15_t")

    n_pixels = 64
    bg_t, bg_y, bg_p, sig_t, sig_y, sig_p, obstacles = _generate_events(
        n_pixels, duration, n_obs, bg_rate=0.4, sig_rate=12.0, seed=seed,
    )
    all_t = np.concatenate([bg_t, sig_t])
    all_y = np.concatenate([bg_y, sig_y])
    counts, fired = _detect(all_t, all_y, n_pixels, duration, bin_ms, thr)

    section_header("Event raster")
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=bg_t, y=bg_y, mode="markers",
        marker=dict(color=COLORS["text_muted"], size=3, opacity=0.55),
        name="Background events",
    ))
    fig.add_trace(go.Scattergl(
        x=sig_t, y=sig_y, mode="markers",
        marker=dict(color=COLORS["highlight"], size=4, opacity=0.95),
        name="Object events",
    ))
    fig.update_xaxes(title="Time (ms)", range=[0, duration])
    fig.update_yaxes(title="Pixel row", range=[0, n_pixels])
    st.plotly_chart(apply_theme(fig, height=320), use_container_width=True)

    section_header("Per-bin event count with detection threshold")
    fig2 = go.Figure()
    centers = (np.arange(len(counts)) + 0.5) * bin_ms
    fig2.add_trace(go.Bar(
        x=centers, y=counts,
        marker_color=[COLORS["danger"] if f else COLORS["primary"] for f in fired],
        name="Events per bin",
    ))
    fig2.add_hline(y=thr, line_color=COLORS["highlight"], line_dash="dash",
                    annotation_text="Threshold", annotation_position="right")
    fig2.update_xaxes(title="Time (ms)")
    fig2.update_yaxes(title="Events / bin")
    st.plotly_chart(apply_theme(fig2, height=240), use_container_width=True)

    fired_idx = np.where(fired)[0]
    first_alarm = None
    if len(fired_idx):
        first_alarm = float(centers[fired_idx[0]])

    total_events = int(len(all_t))
    obj_events = int(len(sig_t))
    metrics_row([
        ("Total events", f"{total_events:,}", COLORS["primary"]),
        ("Object events", f"{obj_events:,}", COLORS["highlight"]),
        ("Detection bins fired", f"{int(fired.sum())}", COLORS["danger"]),
        ("First alarm", f"{first_alarm:.1f} ms" if first_alarm is not None else "—",
         COLORS["success"] if first_alarm is not None else COLORS["text_muted"]),
    ])

    interpretation_block(
        "Event-camera streams give DynNav the option to react at the "
        f"granularity of a {bin_ms}-ms detection bin — far below the "
        "30 Hz cadence of a frame camera. Drop the bin size and the "
        "alarm latency drops further at the cost of more false positives "
        "from background activity. In a real system the threshold is "
        "adapted per scene illumination."
    )
