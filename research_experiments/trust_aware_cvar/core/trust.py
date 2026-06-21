"""
core/trust.py
=============
Trust estimator for the Trust-Aware CVaR Planner.

Trust(cell, t) is a scalar in [0,1] aggregating four sub-signals, mirroring
the four trust components requested in the research spec and reusing the
DynNav security/IDS machinery (Contribution 08) for the anomaly term:

    T = w1*T_calibration + w2*T_sensor_consistency + w3*T_perception + w4*T_anomaly

All sub-scores are in [0,1], 1 = fully trusted.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


@dataclass
class TrustWeights:
    w_calibration: float = 0.30
    w_consistency: float = 0.25
    w_perception: float = 0.25
    w_anomaly: float = 0.20

    def normalized(self):
        s = self.w_calibration + self.w_consistency + self.w_perception + self.w_anomaly
        return TrustWeights(self.w_calibration / s, self.w_consistency / s,
                             self.w_perception / s, self.w_anomaly / s)


def calibration_trust(realized_ece: float, ece_scale: float = 0.30) -> float:
    """Higher ECE -> lower trust. Saturating exponential mapping."""
    return float(np.exp(-realized_ece / ece_scale))


def sensor_consistency_trust(occ_obs: np.ndarray, occ_obs_prev: np.ndarray) -> float:
    """
    Cross-checks consecutive observed occupancy frames (proxy for multi-sensor /
    multi-frame consistency, e.g., LiDAR vs camera vs previous-frame EKF prior
    used in Contribution 02). Large frame-to-frame discrepancy => spoofing/noise.
    """
    if occ_obs_prev is None:
        return 1.0
    diff = np.abs(occ_obs - occ_obs_prev)
    inconsistency = float(diff.mean())
    return float(np.clip(1.0 - 4.0 * inconsistency, 0.0, 1.0))


def perception_reliability_trust(uncertainty_field: np.ndarray) -> float:
    """Global epistemic uncertainty level -> perception reliability score."""
    mean_unc = float(uncertainty_field.mean())
    return float(np.clip(1.0 - 2.0 * mean_unc, 0.0, 1.0))


def adversarial_anomaly_trust(occ_obs: np.ndarray, occ_gt_prior_estimate: np.ndarray,
                               chi2_threshold: float = 6.0) -> float:
    """
    Lightweight chi-squared residual anomaly score, directly modeled on
    DynNav Contribution 08 (chi^2 / CUSUM IDS for sensor spoofing).
    Large residual between observed occupancy and a smoothed prior estimate
    indicates an adversarial / spoofed sensor reading.
    """
    resid = occ_obs - occ_gt_prior_estimate
    chi2_stat = float(np.sum(resid ** 2) / (resid.size * 0.05 ** 2))  # normalized by expected noise var
    score = np.exp(-max(0.0, chi2_stat - chi2_threshold) / chi2_threshold)
    return float(np.clip(score, 0.0, 1.0))


def compute_trust(realized_ece: float, occ_obs: np.ndarray, occ_obs_prev,
                   uncertainty_field: np.ndarray, occ_prior_smoothed: np.ndarray,
                   weights: TrustWeights = None) -> dict:
    weights = (weights or TrustWeights()).normalized()
    t_cal = calibration_trust(realized_ece)
    t_con = sensor_consistency_trust(occ_obs, occ_obs_prev)
    t_per = perception_reliability_trust(uncertainty_field)
    t_adv = adversarial_anomaly_trust(occ_obs, occ_prior_smoothed)
    trust = (weights.w_calibration * t_cal + weights.w_consistency * t_con
             + weights.w_perception * t_per + weights.w_anomaly * t_adv)
    return dict(trust=float(np.clip(trust, 0, 1)), t_calibration=t_cal,
                t_consistency=t_con, t_perception=t_per, t_anomaly=t_adv)
