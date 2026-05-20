"""C21 — PPO: policy learning curve and navigation success rate."""

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


def _ppo_curve(
    n_iters: int, lr_scale: float, kl_clip: float, exploration: float,
    seed: int, n_seeds: int = 4,
):
    """Synthetic PPO learning dynamics.

    The mean reward follows a saturating curve whose rate depends on lr_scale
    and whose plateau depends on kl_clip and exploration. Each seed adds
    Ornstein–Uhlenbeck-style noise on top.
    """
    rng = np.random.default_rng(seed)
    plateau = 0.85 + 0.10 * float(np.clip(kl_clip * 5, 0, 1))
    rate = 0.04 * lr_scale
    iters = np.arange(n_iters)
    mean_curve = plateau * (1.0 - np.exp(-rate * iters))
    # Penalise extreme exploration values
    penalty = 0.25 * (exploration - 0.5) ** 2
    mean_curve = np.clip(mean_curve - penalty, 0.0, 1.0)

    seeds = np.zeros((n_seeds, n_iters))
    for s in range(n_seeds):
        noise = np.zeros(n_iters)
        x = 0.0
        for t in range(n_iters):
            x = 0.85 * x + 0.04 * rng.standard_normal()
            noise[t] = x
        seeds[s] = np.clip(mean_curve + noise, 0.0, 1.05)

    success_rate = mean_curve  # treat reward proxy as success rate too
    success_seeds = np.clip(seeds, 0.0, 1.0)
    return iters, mean_curve, success_rate, seeds, success_seeds


def render(st_ctx=st) -> None:
    explanation_block(
        "C21 — Proximal Policy Optimisation (PPO)",
        "PPO is the workhorse on-policy RL algorithm for continuous control "
        "in robotics: it constrains policy updates to a trust region via "
        "a clipped surrogate objective, which makes learning notably more "
        "stable than vanilla policy gradients. DynNav uses PPO to fine-tune "
        "a navigation policy in simulation before deployment. This panel "
        "shows synthetic learning curves across multiple seeds — the key "
        "diagnostic engineers watch in practice.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 11, key="c21_seed")
    n_iters = c2.slider("Iterations", 50, 400, 200, 10, key="c21_n")
    lr_scale = c3.slider("Learning rate scale", 0.3, 3.0, 1.0, 0.05, key="c21_lr")
    kl_clip = c4.slider("PPO clip ε", 0.05, 0.30, 0.20, 0.01, key="c21_clip")
    expl = c5.slider("Exploration coef.", 0.0, 1.0, 0.4, 0.05, key="c21_e")

    iters, mean_curve, success_rate, seeds, success_seeds = _ppo_curve(
        n_iters, lr_scale, kl_clip, expl, seed,
    )

    # Reward / return curve
    section_header("Episode return across seeds")
    fig = go.Figure()
    for s in range(seeds.shape[0]):
        fig.add_trace(go.Scatter(
            x=iters, y=seeds[s], mode="lines",
            line=dict(color="rgba(34,211,238,0.30)", width=1.2),
            name=f"seed {s+1}", showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=iters, y=mean_curve, mode="lines",
        line=dict(color=COLORS["secondary"], width=3),
        name="Mean reward (over seeds)",
    ))
    # 95% band around the seed distribution
    band_lo = np.percentile(seeds, 5, axis=0)
    band_hi = np.percentile(seeds, 95, axis=0)
    fig.add_trace(go.Scatter(
        x=np.concatenate([iters, iters[::-1]]),
        y=np.concatenate([band_hi, band_lo[::-1]]),
        fill="toself", fillcolor="rgba(34,211,238,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="5–95% band", hoverinfo="skip",
    ))
    fig.update_xaxes(title="Iteration")
    fig.update_yaxes(title="Normalised episode return")
    st.plotly_chart(apply_theme(fig, height=340), use_container_width=True)

    # Navigation success rate
    section_header("Navigation success rate (held-out eval)")
    fig2 = go.Figure()
    for s in range(success_seeds.shape[0]):
        fig2.add_trace(go.Scatter(
            x=iters, y=success_seeds[s], mode="lines",
            line=dict(color="rgba(167,139,250,0.30)", width=1.2),
            showlegend=False,
        ))
    fig2.add_trace(go.Scatter(
        x=iters, y=success_rate, mode="lines",
        line=dict(color=COLORS["accent"], width=3),
        name="Mean success rate",
    ))
    fig2.update_xaxes(title="Iteration")
    fig2.update_yaxes(title="Success rate", range=[0, 1.05])
    st.plotly_chart(apply_theme(fig2, height=240), use_container_width=True)

    final_mean = float(mean_curve[-1])
    seed_std = float(seeds[:, -1].std())
    samples_to_80 = int(np.argmax(mean_curve > 0.80))
    if not (mean_curve > 0.80).any():
        samples_to_80 = -1

    metrics_row([
        ("Final mean return", f"{final_mean:.3f}", COLORS["secondary"]),
        ("Final inter-seed σ", f"{seed_std:.3f}",
         COLORS["success"] if seed_std < 0.05 else COLORS["highlight"]),
        ("Iters to 80% success",
         f"{samples_to_80}" if samples_to_80 >= 0 else "not reached",
         COLORS["primary"]),
        ("Final success rate", f"{success_rate[-1] * 100:.1f}%",
         COLORS["success"]),
    ])

    interpretation_block(
        f"With these hyperparameters, the policy reaches a final return of "
        f"{final_mean:.2f} ± {seed_std:.2f} across seeds. Inter-seed "
        "variance is the diagnostic that matters most for safety: a high "
        "mean with high variance means at least one seed is far from the "
        "optimum and the algorithm is not reliably reproducible. Pushing "
        "exploration too high (slider near 1.0) hurts the plateau; too low "
        "and the policy gets stuck early."
    )
