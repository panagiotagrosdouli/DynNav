"""C11 — Twin-Critic RL: min over two Q-networks for conservative policies."""

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


def _make_two_critics(seed: int, n: int, noise: float):
    """Two synthetic Q-functions over a 1D action space, both noisy estimates
    of the same ground-truth value with slight, independent biases."""
    rng = np.random.default_rng(seed)
    a = np.linspace(-2.0, 2.0, n)
    # Ground truth: a parabola with a small offset peak
    true_q = -0.4 * (a - 0.3) ** 2 + 1.0
    # Two noisy critics: each over-/under-estimates differently
    bias1 = 0.25 * np.sin(2.0 * a + 0.4)
    bias2 = 0.25 * np.cos(1.5 * a - 0.7)
    q1 = true_q + bias1 + noise * rng.standard_normal(n)
    q2 = true_q + bias2 + noise * rng.standard_normal(n)
    return a, true_q, q1, q2


def render(st_ctx=st) -> None:
    explanation_block(
        "C11 — Twin-Critic RL (TD3 / SAC-style)",
        "Value-based deep RL is notoriously prone to over-estimation bias: "
        "the max over noisy Q-estimates is itself biased upwards. TD3 and "
        "SAC mitigate this with twin critics — two independent Q-networks "
        "whose <i>minimum</i> is used as the target. The policy then "
        "optimises a conservative under-estimate, which empirically yields "
        "more stable and safer behaviour. DynNav adopts this for its "
        "RL-augmented local controller.",
    )

    section_header("Interactive controls")
    c1, c2, c3 = st.columns(3)
    seed = c1.slider("Seed", 0, 50, 7, key="c11_seed")
    noise = c2.slider("Critic noise σ", 0.0, 0.6, 0.18, 0.01, key="c11_n")
    show_optimistic = c3.toggle("Show optimistic policy", value=True, key="c11_opt")

    n = 100
    a, true_q, q1, q2 = _make_two_critics(seed, n, noise)
    conservative = np.minimum(q1, q2)
    optimistic = np.maximum(q1, q2)

    a_true = float(a[np.argmax(true_q)])
    a_cons = float(a[np.argmax(conservative)])
    a_opt = float(a[np.argmax(optimistic)])
    a_avg = float(a[np.argmax((q1 + q2) / 2)])

    section_header("Q-value curves and policy choices")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=a, y=true_q, name="Ground-truth Q",
                              line=dict(color=COLORS["success"], width=2)))
    fig.add_trace(go.Scatter(x=a, y=q1, name="Critic Q₁",
                              line=dict(color=COLORS["primary"], width=1.6, dash="dot")))
    fig.add_trace(go.Scatter(x=a, y=q2, name="Critic Q₂",
                              line=dict(color=COLORS["secondary"], width=1.6, dash="dot")))
    fig.add_trace(go.Scatter(x=a, y=conservative,
                              name="min(Q₁, Q₂)  ← conservative target",
                              line=dict(color=COLORS["accent"], width=3)))
    fig.add_vline(x=a_true, line_color=COLORS["success"], line_dash="dash",
                   annotation_text="argmax true", annotation_position="top")
    fig.add_vline(x=a_cons, line_color=COLORS["accent"], line_dash="dash",
                   annotation_text="conservative π", annotation_position="bottom")
    if show_optimistic:
        fig.add_trace(go.Scatter(x=a, y=optimistic,
                                  name="max(Q₁, Q₂)  ← optimistic target",
                                  line=dict(color=COLORS["danger"], width=2, dash="dashdot")))
        fig.add_vline(x=a_opt, line_color=COLORS["danger"], line_dash="dot",
                       annotation_text="optimistic π", annotation_position="top")
    fig.update_xaxes(title="Action")
    fig.update_yaxes(title="Q-value")
    st.plotly_chart(apply_theme(fig, height=420), use_container_width=True)

    err_cons = abs(a_cons - a_true)
    err_opt = abs(a_opt - a_true)
    err_avg = abs(a_avg - a_true)
    bias_opt = float(optimistic.max() - true_q.max())
    bias_cons = float(conservative.max() - true_q.max())

    metrics_row([
        ("Conservative π action", f"{a_cons:+.2f}", COLORS["accent"]),
        ("Optimistic π action", f"{a_opt:+.2f}", COLORS["danger"]),
        ("True optimum", f"{a_true:+.2f}", COLORS["success"]),
        ("Conservative |error|", f"{err_cons:.2f}", COLORS["primary"]),
        ("Optimistic |error|", f"{err_opt:.2f}", COLORS["primary"]),
    ])
    st.write("")
    metrics_row([
        ("Optimistic value bias", f"{bias_opt:+.3f}", COLORS["danger"]),
        ("Conservative value bias", f"{bias_cons:+.3f}", COLORS["success"]),
        ("Mean-critic action error", f"{err_avg:.2f}", COLORS["text_muted"]),
    ])

    interpretation_block(
        f"The optimistic estimator over-estimates the true maximum by "
        f"<b>{bias_opt:+.3f}</b>, while the conservative twin-critic "
        f"<i>under</i>-estimates it by <b>{bias_cons:+.3f}</b>. Crucially, "
        "this conservative bias rarely picks a catastrophic action: the "
        "conservative π's action error is typically lower than the "
        "optimistic π's, especially at high noise σ. Try σ ≥ 0.4 to see "
        "the optimistic policy collapse onto a noisy peak that does not "
        "track ground truth."
    )
