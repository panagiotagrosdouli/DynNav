"""Probabilistic risk-map evaluation for Contribution 12.

Diffusion occupancy maps are useful only if their predicted probabilities and
uncertainty are meaningful. This module evaluates predicted occupancy/risk maps
against realized future occupancy using simple, auditable metrics:

- Brier score,
- negative log likelihood,
- binary accuracy at threshold,
- empirical coverage of high-risk masks,
- CVaR conservatism gap.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class RiskMapMetrics:
    brier_score: float
    nll: float
    accuracy_at_05: float
    high_risk_precision: float
    high_risk_recall: float
    cvar_conservatism_gap: float
    mean_predicted_risk: float
    mean_observed_occupancy: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def _validate_maps(predicted_prob: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(predicted_prob, dtype=float)
    y = np.asarray(observed, dtype=float)
    if p.shape != y.shape:
        raise ValueError(f"predicted and observed maps must have same shape, got {p.shape} and {y.shape}")
    if p.size == 0:
        raise ValueError("maps must not be empty")
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    y = np.clip(y, 0.0, 1.0)
    return p, y


def brier_score(predicted_prob: np.ndarray, observed: np.ndarray) -> float:
    p, y = _validate_maps(predicted_prob, observed)
    return float(np.mean((p - y) ** 2))


def negative_log_likelihood(predicted_prob: np.ndarray, observed: np.ndarray) -> float:
    p, y = _validate_maps(predicted_prob, observed)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def high_risk_precision_recall(
    predicted_prob: np.ndarray,
    observed: np.ndarray,
    threshold: float = 0.65,
) -> tuple[float, float]:
    p, y = _validate_maps(predicted_prob, observed)
    pred_mask = p >= threshold
    obs_mask = y >= 0.5
    tp = float(np.logical_and(pred_mask, obs_mask).sum())
    fp = float(np.logical_and(pred_mask, ~obs_mask).sum())
    fn = float(np.logical_and(~pred_mask, obs_mask).sum())
    precision = tp / max(1.0, tp + fp)
    recall = tp / max(1.0, tp + fn)
    return float(precision), float(recall)


def evaluate_risk_map(
    predicted_prob: np.ndarray,
    observed: np.ndarray,
    cvar_map: np.ndarray | None = None,
    high_risk_threshold: float = 0.65,
) -> RiskMapMetrics:
    p, y = _validate_maps(predicted_prob, observed)
    cvar = np.asarray(cvar_map, dtype=float) if cvar_map is not None else p
    if cvar.shape != p.shape:
        raise ValueError("cvar_map must have the same shape as predicted_prob")
    cvar = np.clip(cvar, 0.0, 1.0)
    pred_binary = p >= 0.5
    obs_binary = y >= 0.5
    precision, recall = high_risk_precision_recall(p, y, threshold=high_risk_threshold)
    return RiskMapMetrics(
        brier_score=brier_score(p, y),
        nll=negative_log_likelihood(p, y),
        accuracy_at_05=float(np.mean(pred_binary == obs_binary)),
        high_risk_precision=precision,
        high_risk_recall=recall,
        cvar_conservatism_gap=float(np.mean(cvar - p)),
        mean_predicted_risk=float(np.mean(p)),
        mean_observed_occupancy=float(np.mean(y)),
    )
