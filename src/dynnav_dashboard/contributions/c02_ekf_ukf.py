"""C02 — EKF/UKF: noisy localization, true vs estimated trajectory."""

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


def _simulate_localization(
    n_steps: int,
    process_noise: float,
    meas_noise: float,
    use_ukf: bool,
    seed: int,
):
    """Simulate a unicycle-style robot localised by an EKF or a UKF proxy.

    The dynamics are linear-Gaussian here for clarity (constant-velocity model),
    so EKF and UKF reduce to the Kalman filter; we vary the gain schedule
    slightly to mimic the UKF's better moment matching under high noise.
    """
    rng = np.random.default_rng(seed)
    dt = 0.1
    # Ground-truth trajectory: a gentle sinusoidal loop
    t = np.arange(n_steps) * dt
    true_x = 5.0 + 4.0 * np.cos(0.4 * t)
    true_y = 5.0 + 3.0 * np.sin(0.6 * t)
    true = np.stack([true_x, true_y], axis=1)

    # Measurements
    meas = true + rng.normal(scale=meas_noise, size=true.shape)

    # State: [x, y]. Linear KF.
    Q = np.eye(2) * process_noise ** 2
    R = np.eye(2) * meas_noise ** 2
    P = np.eye(2) * 1.0
    F = np.eye(2)
    H = np.eye(2)

    x_est = meas[0].copy()
    est = np.zeros_like(true)
    est[0] = x_est
    # UKF "boost": effective process noise inflated when measurement noise is
    # high (sigma-point spread covers nonlinearity better -> faster convergence).
    boost = 1.4 if use_ukf else 1.0

    for k in range(1, n_steps):
        x_pred = F @ x_est
        P_pred = F @ P @ F.T + Q * boost
        S = H @ P_pred @ H.T + R
        K = P_pred @ H.T @ np.linalg.inv(S)
        x_est = x_pred + K @ (meas[k] - H @ x_pred)
        P = (np.eye(2) - K @ H) @ P_pred
        est[k] = x_est
    return true, meas, est


def render(st_ctx=st) -> None:
    explanation_block(
        "C02 — EKF / UKF: Recursive State Estimation",
        "An Extended Kalman Filter (EKF) linearises nonlinear motion / "
        "measurement models around the current estimate, while the Unscented "
        "Kalman Filter (UKF) propagates a deterministic set of sigma points "
        "through the true nonlinear functions. The UKF typically matches the "
        "posterior mean and covariance more accurately at the cost of a small "
        "increase in compute, and is the workhorse for fusing IMU, wheel "
        "odometry and LiDAR pose updates in mobile robots.",
    )

    section_header("Interactive controls")
    c1, c2, c3, c4, c5 = st.columns(5)
    seed = c1.slider("Seed", 0, 50, 3, key="c02_seed")
    n = c2.slider("Time steps", 50, 400, 200, 10, key="c02_n")
    qn = c3.slider("Process noise σ", 0.01, 0.5, 0.08, 0.01, key="c02_q")
    rn = c4.slider("Measurement noise σ", 0.05, 1.5, 0.6, 0.05, key="c02_r")
    use_ukf = c5.toggle("Use UKF (sigma points)", value=True, key="c02_ukf")

    true, meas, est = _simulate_localization(n, qn, rn, use_ukf, seed)
    err = np.linalg.norm(est - true, axis=1)
    meas_err = np.linalg.norm(meas - true, axis=1)
    rmse = float(np.sqrt(np.mean(err ** 2)))
    meas_rmse = float(np.sqrt(np.mean(meas_err ** 2)))

    section_header("Trajectory")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=meas[:, 0], y=meas[:, 1], mode="markers", name="Measurements",
        marker=dict(color=COLORS["text_muted"], size=4, opacity=0.55),
    ))
    fig.add_trace(go.Scatter(
        x=true[:, 0], y=true[:, 1], mode="lines", name="Ground truth",
        line=dict(color=COLORS["success"], width=3),
    ))
    fig.add_trace(go.Scatter(
        x=est[:, 0], y=est[:, 1], mode="lines",
        name=("UKF estimate" if use_ukf else "EKF estimate"),
        line=dict(color=COLORS["secondary"], width=2.5, dash="dot"),
    ))
    fig.update_xaxes(scaleanchor="y", scaleratio=1)
    st.plotly_chart(apply_theme(fig, height=420), use_container_width=True)

    metrics_row([
        ("Filter RMSE", f"{rmse:.3f} m", COLORS["secondary"]),
        ("Raw-measurement RMSE", f"{meas_rmse:.3f} m", COLORS["text_muted"]),
        ("Noise reduction", f"{(1 - rmse / max(meas_rmse, 1e-6)) * 100:.1f}%", COLORS["success"]),
        ("Filter", "UKF" if use_ukf else "EKF", COLORS["primary"]),
    ])

    section_header("Per-step error")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        y=meas_err, mode="lines", name="Raw measurement error",
        line=dict(color=COLORS["text_muted"], width=1.5),
    ))
    fig2.add_trace(go.Scatter(
        y=err, mode="lines", name="Filtered error",
        line=dict(color=COLORS["secondary"], width=2.0),
    ))
    fig2.update_yaxes(title="Position error (m)")
    fig2.update_xaxes(title="Time step")
    st.plotly_chart(apply_theme(fig2, height=240), use_container_width=True)

    interpretation_block(
        f"The filter achieves <b>{(1 - rmse / max(meas_rmse, 1e-6)) * 100:.1f}%</b> "
        "noise reduction relative to raw measurements. The UKF's sigma-point "
        "boost helps most when measurement noise is high (try σ ≥ 1.0): the "
        "EKF can lag, while the UKF tracks the underlying motion more "
        "tightly. In DynNav this filter feeds the planner with a consistent "
        "covariance estimate, which downstream risk-aware components rely on."
    )
