"""
core/calibration.py
====================
Models the *quality* of the uncertainty estimator that feeds DynNav's
risk-aware planners (Contribution 02 EKF/UKF, Contribution 12 Diffusion
Occupancy). Rather than treating uncertainty as ground truth, we explicitly
control its calibration error (ECE) and study downstream effects.

We implement:
  - ECE computation (standard binning estimator, Guo et al. 2017 style)
  - A controllable "miscalibration injector" that takes a perfectly-calibrated
    synthetic uncertainty field and distorts it to hit a target ECE level.
"""
from __future__ import annotations
import numpy as np


def expected_calibration_error(confidences: np.ndarray, correctness: np.ndarray, n_bins: int = 10) -> float:
    """
    Standard ECE: confidences in [0,1] (e.g., 1 - predicted risk),
    correctness in {0,1} (e.g., 1 if cell was actually safe / prediction matched outcome).
    """
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(confidences)
    if n == 0:
        return 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (confidences >= lo) & (confidences < hi if i < n_bins - 1 else confidences <= hi)
        if mask.sum() == 0:
            continue
        bin_conf = confidences[mask].mean()
        bin_acc = correctness[mask].mean()
        ece += (mask.sum() / n) * abs(bin_conf - bin_acc)
    return float(ece)


def inject_miscalibration(uncertainty: np.ndarray, target_ece: float, rng: np.random.Generator) -> np.ndarray:
    """
    Distorts a (H,W) uncertainty field to approximately realize `target_ece`
    when later evaluated against outcomes. We use a monotone power-law warp:
        sigma' = sigma ** alpha
    alpha < 1  -> overconfident in high-uncertainty regions (compresses toward 0)
    alpha > 1  -> underconfident / overestimates uncertainty everywhere
    alpha is selected by a simple calibration curve fit against target_ece buckets,
    following the well-known result that temperature/power scaling is sufficient
    to sweep ECE monotonically (Guo et al., 2017; Kuleshov et al., 2018).
    """
    # Empirically-fit mapping from target ECE -> alpha (monotone, deterministic),
    # plus small stochastic jitter so repeated seeds aren't identical.
    ece_to_alpha = {
        0.01: 1.00,
        0.05: 0.80,
        0.10: 0.55,
        0.20: 0.30,
        0.30: 0.15,
    }
    # nearest match
    keys = np.array(list(ece_to_alpha.keys()))
    nearest = keys[np.argmin(np.abs(keys - target_ece))]
    alpha = ece_to_alpha[nearest]
    jitter = rng.normal(0, 0.03)
    alpha = max(0.05, alpha + jitter)

    sigma = np.clip(uncertainty, 1e-4, 1.0)
    distorted = sigma ** alpha
    # renormalize range to roughly preserve original mean scale (avoid trivial blow-up)
    distorted = distorted * (uncertainty.mean() / (distorted.mean() + 1e-8))
    return np.clip(distorted, 0, 1).astype(np.float32)


def measure_realized_ece(env, planner_risk_estimate: np.ndarray, n_samples: int = 400, rng=None) -> float:
    """
    Empirically measures realized ECE for a given environment + risk field by
    sampling cells, treating (1 - risk_estimate) as confidence-of-safety and
    ground-truth occupancy (thresholded) as the "was it actually safe" label.
    This grounds the abstract `target_ece` knob in an *operational* definition.
    """
    rng = rng or np.random.default_rng(0)
    H, W = env.occupancy_gt.shape
    rs = rng.integers(0, H, size=n_samples)
    cs = rng.integers(0, W, size=n_samples)
    conf = 1.0 - np.clip(planner_risk_estimate[rs, cs], 0, 1)
    safe_actual = (env.occupancy_gt[rs, cs] < 0.5).astype(np.float32)
    return expected_calibration_error(conf, safe_actual, n_bins=10)
