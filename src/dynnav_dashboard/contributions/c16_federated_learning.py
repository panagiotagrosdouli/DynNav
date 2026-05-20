"""C16 — Federated Learning: per-client and global validation error."""

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


def _run_federated(
    n_clients: int, n_rounds: int, local_epochs: int, lr: float,
    heterogeneity: float, seed: int, drop_rate: float,
):
    """Simulate FedAvg on a 1D scalar regression problem.

    Each client has a noisy local dataset drawn around a slightly shifted
    optimum (heterogeneity). FedAvg aggregates the local parameters at each
    round. The 'global validation' error is computed on a held-out set drawn
    from the average distribution.
    """
    rng = np.random.default_rng(seed)
    centers = rng.normal(loc=0.0, scale=heterogeneity, size=n_clients)
    # Local data
    n_per_client = 30
    clients_x = [rng.normal(loc=c, scale=1.0, size=n_per_client) for c in centers]
    val_x = rng.normal(loc=0.0, scale=1.0, size=200)

    theta_global = float(rng.normal(0.0, 1.0))
    history_global = []
    history_clients = [[] for _ in range(n_clients)]
    history_centralised = []
    theta_central = float(rng.normal(0.0, 1.0))

    for r in range(n_rounds):
        # Local updates (a few gradient steps each)
        local_thetas = []
        for k, x in enumerate(clients_x):
            theta_local = theta_global
            for _ in range(local_epochs):
                grad = 2.0 * (theta_local - x.mean())  # MSE w.r.t. local mean
                theta_local -= lr * grad
            local_thetas.append(theta_local)
            err = float(np.mean((val_x - theta_local) ** 2))
            history_clients[k].append(err)
        # Client dropout
        keep = rng.random(n_clients) > drop_rate
        if not keep.any():
            keep[0] = True
        theta_global = float(np.mean(np.array(local_thetas)[keep]))
        global_err = float(np.mean((val_x - theta_global) ** 2))
        history_global.append(global_err)

        # Centralised baseline: SGD on the union of all clients' data
        all_x = np.concatenate(clients_x)
        for _ in range(local_epochs * n_clients):  # comparable compute
            grad = 2.0 * (theta_central - all_x.mean())
            theta_central -= lr * grad
        history_centralised.append(float(np.mean((val_x - theta_central) ** 2)))

    return history_global, history_clients, history_centralised


def render(st_ctx=st) -> None:
    explanation_block(
        "C16 — Federated Learning across a Robot Fleet",
        "Federated Learning lets a fleet of robots improve a shared model "
        "without exchanging raw data — each robot trains locally and only "
        "model parameters are aggregated (FedAvg). Convergence is "
        "slower than centralised training and sensitive to data "
        "heterogeneity and client dropout, but it preserves privacy and "
        "saves bandwidth. DynNav uses FL for perception finetuning across "
        "deployments.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 7, key="c16_seed")
    n_clients = c2.slider("Robots (clients)", 2, 12, 6, key="c16_c")
    n_rounds = c3.slider("Rounds", 5, 50, 25, key="c16_r")
    heterogeneity = c4.slider("Data heterogeneity", 0.0, 2.0, 0.6, 0.05, key="c16_h")
    drop_rate = c5.slider("Client drop-out", 0.0, 0.7, 0.15, 0.05, key="c16_d")

    hg, hc, hcen = _run_federated(
        n_clients=n_clients,
        n_rounds=n_rounds,
        local_epochs=4,
        lr=0.08,
        heterogeneity=heterogeneity,
        seed=seed,
        drop_rate=drop_rate,
    )

    section_header("Validation error per round")
    fig = go.Figure()
    palette = [
        "rgba(59,130,246,0.45)", "rgba(34,211,238,0.45)",
        "rgba(167,139,250,0.45)", "rgba(245,158,11,0.45)",
        "rgba(34,197,94,0.45)", "rgba(239,68,68,0.45)",
        "rgba(244,114,182,0.45)", "rgba(253,224,71,0.45)",
        "rgba(110,231,183,0.45)", "rgba(125,211,252,0.45)",
        "rgba(196,181,253,0.45)", "rgba(254,202,202,0.45)",
    ]
    for k, hist in enumerate(hc):
        fig.add_trace(go.Scatter(
            y=hist, mode="lines", name=f"Robot {k+1} local val",
            line=dict(color=palette[k % len(palette)], width=1.4),
            showlegend=(k < 4),
        ))
    fig.add_trace(go.Scatter(
        y=hg, mode="lines+markers", name="FedAvg global val",
        line=dict(color=COLORS["secondary"], width=3),
        marker=dict(color=COLORS["secondary"], size=5),
    ))
    fig.add_trace(go.Scatter(
        y=hcen, mode="lines", name="Centralised baseline",
        line=dict(color=COLORS["success"], width=2.5, dash="dot"),
    ))
    fig.update_xaxes(title="Round")
    fig.update_yaxes(title="Validation MSE")
    st.plotly_chart(apply_theme(fig, height=420), use_container_width=True)

    final_global = float(hg[-1])
    final_centralised = float(hcen[-1])
    initial = float(hg[0])
    metrics_row([
        ("Initial val MSE", f"{initial:.4f}", COLORS["text_muted"]),
        ("Final FedAvg MSE", f"{final_global:.4f}", COLORS["secondary"]),
        ("Final centralised MSE", f"{final_centralised:.4f}", COLORS["success"]),
        ("Convergence ratio",
         f"{(initial - final_global) / max(initial - final_centralised, 1e-6):.2f}×",
         COLORS["primary"]),
    ])

    interpretation_block(
        f"FedAvg reached MSE = {final_global:.4f} after {n_rounds} rounds; "
        f"the centralised baseline reached {final_centralised:.4f}. With "
        "high heterogeneity, FedAvg lags more — try slider ≥ 1.5 to see "
        "the gap widen. Increased client drop-out further slows convergence "
        "but in DynNav this is the realistic regime (robots come online and "
        "go offline). FedAvg still beats per-client training because the "
        "aggregated model generalises across deployment sites."
    )
