"""NeRF uncertainty evaluation utilities for Contribution 24.

NeRF-derived uncertainty should be evaluated as a navigation signal, not only
visualized as a heatmap. This module provides lightweight, reproducible metrics:

- Brier score and negative log likelihood for uncertainty-as-risk calibration,
- expected calibration error (ECE),
- OOD AUROC for unknown / poorly observed cells,
- novel-view uncertainty gap,
- exploration priority quality,
- planning safety gain proxy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class NeRFUncertaintyMetrics:
    scenario: str
    brier_score: float
    nll: float
    ece: float
    ood_auroc: float
    novel_view_uncertainty_gap: float
    exploration_precision_at_k: float
    planning_safety_gain: float
    mean_uncertainty_known: float
    mean_uncertainty_unknown: float

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


def _clip_prob(x: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(x, dtype=float), 1e-6, 1.0 - 1e-6)


def brier_score(prob: np.ndarray, target: np.ndarray) -> float:
    p = _clip_prob(prob)
    y = np.asarray(target, dtype=float)
    if p.shape != y.shape:
        raise ValueError("prob and target must have the same shape")
    return float(np.mean((p - y) ** 2))


def negative_log_likelihood(prob: np.ndarray, target: np.ndarray) -> float:
    p = _clip_prob(prob)
    y = np.asarray(target, dtype=float)
    if p.shape != y.shape:
        raise ValueError("prob and target must have the same shape")
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def expected_calibration_error(prob: np.ndarray, target: np.ndarray, n_bins: int = 10) -> float:
    p = _clip_prob(prob).ravel()
    y = np.asarray(target, dtype=float).ravel()
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (p >= lo) & (p < hi if hi < 1.0 else p <= hi)
        if not np.any(mask):
            continue
        conf = float(np.mean(p[mask]))
        freq = float(np.mean(y[mask]))
        ece += float(mask.mean()) * abs(conf - freq)
    return float(ece)


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    s = np.asarray(scores, dtype=float).ravel()
    y = np.asarray(labels, dtype=int).ravel()
    pos = s[y == 1]
    neg = s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    # Mann-Whitney style AUROC.
    wins = 0.0
    total = 0.0
    for ps in pos:
        wins += float(np.sum(ps > neg)) + 0.5 * float(np.sum(ps == neg))
        total += len(neg)
    return float(wins / max(1.0, total))


def precision_at_k(scores: np.ndarray, target: np.ndarray, k_fraction: float = 0.1) -> float:
    s = np.asarray(scores, dtype=float).ravel()
    y = np.asarray(target, dtype=float).ravel() >= 0.5
    k = max(1, int(len(s) * k_fraction))
    idx = np.argsort(s)[-k:]
    return float(np.mean(y[idx]))


def shortest_risk_path_cost(risk: np.ndarray, start: tuple[int, int], goal: tuple[int, int]) -> float:
    """Small dynamic-programming proxy for right/down grid path risk."""
    arr = np.asarray(risk, dtype=float)
    H, W = arr.shape
    sy, sx = start
    gy, gx = goal
    if sy > gy or sx > gx:
        raise ValueError("This lightweight proxy assumes goal is down/right of start")
    dp = np.full((H, W), np.inf)
    dp[sy, sx] = arr[sy, sx]
    for y in range(sy, gy + 1):
        for x in range(sx, gx + 1):
            if y == sy and x == sx:
                continue
            best = np.inf
            if y > sy:
                best = min(best, dp[y - 1, x])
            if x > sx:
                best = min(best, dp[y, x - 1])
            dp[y, x] = best + arr[y, x]
    return float(dp[gy, gx])


def synthetic_uncertainty_case(seed: int, size: int = 48, ood_shift: bool = False) -> dict[str, np.ndarray]:
    """Create synthetic known/unknown/novel-view maps for deterministic evaluation."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    observed = ((x - size * 0.35) ** 2 + (y - size * 0.45) ** 2) < (size * 0.28) ** 2
    if ood_shift:
        observed = ((x - size * 0.25) ** 2 + (y - size * 0.35) ** 2) < (size * 0.18) ** 2
    unknown = ~observed
    hazard = (((x - size * 0.72) ** 2 + (y - size * 0.65) ** 2) < (size * 0.15) ** 2).astype(float)
    risk_target = np.logical_or(unknown, hazard > 0.5).astype(float)

    distance_from_center = np.sqrt((x - size * 0.35) ** 2 + (y - size * 0.45) ** 2) / size
    uncertainty = 0.15 + 0.70 * unknown.astype(float) + 0.25 * hazard
    uncertainty += 0.20 * distance_from_center + rng.normal(0.0, 0.05, (size, size))
    uncertainty = np.clip(uncertainty, 0.01, 0.99)

    novel_view_unc = np.clip(uncertainty + 0.20 * unknown.astype(float) + rng.normal(0.0, 0.03, (size, size)), 0.01, 0.99)
    entropy_baseline = np.clip(0.5 + rng.normal(0.0, 0.12, (size, size)), 0.01, 0.99)
    return {
        "uncertainty": uncertainty,
        "novel_view_uncertainty": novel_view_unc,
        "entropy_baseline": entropy_baseline,
        "risk_target": risk_target,
        "unknown": unknown.astype(float),
        "hazard": hazard,
    }


def evaluate_nerf_uncertainty_case(scenario: str, seed: int, ood_shift: bool = False) -> NeRFUncertaintyMetrics:
    case = synthetic_uncertainty_case(seed, ood_shift=ood_shift)
    unc = case["uncertainty"]
    target = case["risk_target"]
    unknown = case["unknown"]
    novel = case["novel_view_uncertainty"]
    entropy = case["entropy_baseline"]

    start = (2, 2)
    goal = (unc.shape[0] - 3, unc.shape[1] - 3)
    entropy_cost = shortest_risk_path_cost(entropy, start, goal)
    nerf_cost = shortest_risk_path_cost(unc, start, goal)
    safety_gain = float((entropy_cost - nerf_cost) / max(1e-6, entropy_cost))

    known_mask = unknown < 0.5
    unknown_mask = unknown >= 0.5
    return NeRFUncertaintyMetrics(
        scenario=scenario,
        brier_score=brier_score(unc, target),
        nll=negative_log_likelihood(unc, target),
        ece=expected_calibration_error(unc, target),
        ood_auroc=auroc(unc, unknown),
        novel_view_uncertainty_gap=float(np.mean(novel[unknown_mask]) - np.mean(novel[known_mask])),
        exploration_precision_at_k=precision_at_k(unc, unknown, k_fraction=0.10),
        planning_safety_gain=safety_gain,
        mean_uncertainty_known=float(np.mean(unc[known_mask])),
        mean_uncertainty_unknown=float(np.mean(unc[unknown_mask])),
    )
