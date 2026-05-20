"""C22 — Curriculum RL: flat training vs curriculum training comparison."""

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


def _train_curves(
    n_iters: int, difficulty_final: float, n_stages: int, seed: int, noise: float,
):
    """Synthetic flat-vs-curriculum learning curves.

    Flat: target difficulty from step 0. Curriculum: difficulty rises in steps.
    The achievable success rate at each iteration depends on the gap between
    the policy's current capability and the requested difficulty.
    """
    rng = np.random.default_rng(seed)
    iters = np.arange(n_iters)

    # Flat: trains directly at final difficulty -> slow start, may plateau low.
    capability_flat = np.zeros(n_iters)
    capability_curr = np.zeros(n_iters)
    cap_f = 0.05
    cap_c = 0.05

    # Stage schedule
    stage_difficulty = np.linspace(0.25, difficulty_final, n_stages)
    stage_length = max(1, n_iters // n_stages)

    for t in range(n_iters):
        # Flat: target = difficulty_final, gain proportional to gap below it
        gap_f = max(0.0, difficulty_final - cap_f)
        cap_f += 0.012 * gap_f + 0.005 * rng.standard_normal() * noise
        capability_flat[t] = np.clip(cap_f, 0.0, 1.0)
        # Curriculum: current stage target
        stage_idx = min(t // stage_length, n_stages - 1)
        target = stage_difficulty[stage_idx]
        gap_c = max(0.0, target - cap_c)
        # higher learning gain because target is reachable
        cap_c += 0.022 * gap_c + 0.006 * rng.standard_normal() * noise
        capability_curr[t] = np.clip(cap_c, 0.0, 1.0)

    # Success rate at the final difficulty = sigmoid(capability - difficulty)
    success_flat = 1.0 / (1.0 + np.exp(-(capability_flat - difficulty_final) * 8.0))
    success_curr = 1.0 / (1.0 + np.exp(-(capability_curr - difficulty_final) * 8.0))
    return iters, capability_flat, capability_curr, success_flat, success_curr, stage_difficulty, stage_length


def render(st_ctx=st) -> None:
    explanation_block(
        "C22 — Curriculum RL: Training in Stages of Rising Difficulty",
        "When the final task is too hard for an untrained policy to reach "
        "any positive reward, RL stalls. A curriculum starts the agent on "
        "easy variants and gradually raises the difficulty as competence "
        "builds, letting the policy bootstrap onto useful behaviour. "
        "DynNav curricula start with sparse static maps and progress to "
        "dense dynamic environments with adversarial neighbours.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 5, key="c22_seed")
    n_iters = c2.slider("Iterations", 100, 600, 300, 10, key="c22_n")
    dif = c3.slider("Final task difficulty", 0.3, 1.0, 0.85, 0.05, key="c22_d")
    n_stages = c4.slider("Curriculum stages", 2, 8, 4, key="c22_s")
    noise = c5.slider("Training noise", 0.0, 1.5, 0.6, 0.1, key="c22_noise")

    (iters, cap_flat, cap_curr, succ_flat, succ_curr,
     stage_d, stage_len) = _train_curves(n_iters, dif, n_stages, seed, noise)

    section_header("Training capability — flat vs curriculum")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iters, y=cap_flat, name="Flat training",
        line=dict(color=COLORS["danger"], width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=iters, y=cap_curr, name="Curriculum training",
        line=dict(color=COLORS["success"], width=3),
    ))
    # Stage boundaries
    for s in range(1, n_stages):
        fig.add_vline(x=s * stage_len, line_color="rgba(255,255,255,0.18)",
                       line_dash="dot")
    fig.add_hline(y=dif, line_color=COLORS["highlight"], line_dash="dash",
                   annotation_text="Final difficulty", annotation_position="left")
    fig.update_xaxes(title="Iteration")
    fig.update_yaxes(title="Policy capability", range=[0, 1.05])
    st.plotly_chart(apply_theme(fig, height=340), use_container_width=True)

    section_header("Success rate at the final (hard) task")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=iters, y=succ_flat, name="Flat",
        line=dict(color=COLORS["danger"], width=2.5),
    ))
    fig2.add_trace(go.Scatter(
        x=iters, y=succ_curr, name="Curriculum",
        line=dict(color=COLORS["success"], width=3),
    ))
    fig2.update_xaxes(title="Iteration")
    fig2.update_yaxes(title="Success rate", range=[0, 1.05])
    st.plotly_chart(apply_theme(fig2, height=240), use_container_width=True)

    final_flat = float(succ_flat[-1])
    final_curr = float(succ_curr[-1])
    iters_to_50 = np.argmax(succ_curr > 0.5)
    iters_to_50 = int(iters_to_50) if (succ_curr > 0.5).any() else -1

    metrics_row([
        ("Final flat success", f"{final_flat * 100:.1f}%", COLORS["danger"]),
        ("Final curriculum success",
         f"{final_curr * 100:.1f}%", COLORS["success"]),
        ("Curriculum advantage",
         f"{(final_curr - final_flat) * 100:+.1f} pts", COLORS["primary"]),
        ("Iters to 50% (curr.)",
         f"{iters_to_50}" if iters_to_50 >= 0 else "not reached",
         COLORS["secondary"]),
    ])

    interpretation_block(
        f"With these settings, curriculum training closes "
        f"{(final_curr - final_flat) * 100:+.1f} percentage points of "
        "success-rate gap over flat training. The advantage is largest "
        "when the final difficulty is high — try sliding it to 1.0 and "
        "watch the flat curve flatten near the bottom while the curriculum "
        "still climbs. Fewer stages reduce smoothing; more stages slow the "
        "early progression but increase the chance of finishing strong."
    )
