"""Uncertainty calibration utilities for Contribution 02.

The original C02 result shows an important scientific point: predicted
uncertainty can be informative without being probabilistically calibrated.
This module adds a lightweight calibration layer so uncertainty values can be
mapped to more reliable error scales before they are used by downstream planners.

The code is dependency-light and can be used with CSV outputs from any model that
produces:

- a prediction,
- a target or observed value,
- a predicted uncertainty estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


ArrayLike = Iterable[float] | np.ndarray


@dataclass(frozen=True)
class CalibrationReport:
    """Summary statistics for uncertainty calibration quality."""

    n: int
    mae: float
    pearson_uncertainty_error: float
    spearman_uncertainty_error: float
    ece_abs_error: float
    coverage_1sigma: float
    coverage_2sigma: float
    coverage_3sigma: float
    mean_sigma: float
    mean_abs_error: float


def _as_1d(values: ArrayLike, name: str) -> np.ndarray:
    arr = np.asarray(list(values) if not isinstance(values, np.ndarray) else values, dtype=float).reshape(-1)
    if arr.size == 0:
        raise ValueError(f"{name} must contain at least one value.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values.")
    return arr


def absolute_error(prediction: ArrayLike, target: ArrayLike) -> np.ndarray:
    pred = _as_1d(prediction, "prediction")
    tgt = _as_1d(target, "target")
    if pred.shape != tgt.shape:
        raise ValueError("prediction and target must have the same shape.")
    return np.abs(pred - tgt)


def rankdata(values: np.ndarray) -> np.ndarray:
    """Small rankdata implementation with average ranks for ties."""
    order = np.argsort(values)
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = 0.5 * (i + j) + 1.0
        ranks[order[i : j + 1]] = avg_rank
        i = j + 1
    return ranks


def safe_corrcoef(x: ArrayLike, y: ArrayLike) -> float:
    x_arr = _as_1d(x, "x")
    y_arr = _as_1d(y, "y")
    if x_arr.shape != y_arr.shape:
        raise ValueError("x and y must have the same shape.")
    if x_arr.size < 2 or np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return float("nan")
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def spearman_corr(x: ArrayLike, y: ArrayLike) -> float:
    return safe_corrcoef(rankdata(_as_1d(x, "x")), rankdata(_as_1d(y, "y")))


def coverage(abs_error: ArrayLike, sigma: ArrayLike, k: float) -> float:
    err = _as_1d(abs_error, "abs_error")
    sig = np.maximum(_as_1d(sigma, "sigma"), 1e-12)
    if err.shape != sig.shape:
        raise ValueError("abs_error and sigma must have the same shape.")
    return float(np.mean(err <= k * sig))


def ece_abs_error(abs_error: ArrayLike, sigma: ArrayLike, n_bins: int = 10) -> float:
    """Expected calibration error for absolute error versus predicted sigma.

    The metric bins examples by predicted sigma and compares mean predicted sigma
    with mean observed absolute error in each bin.
    """
    err = _as_1d(abs_error, "abs_error")
    sig = np.maximum(_as_1d(sigma, "sigma"), 1e-12)
    if err.shape != sig.shape:
        raise ValueError("abs_error and sigma must have the same shape.")
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1.")

    quantiles = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.quantile(sig, quantiles)
    total = len(sig)
    ece = 0.0
    for i in range(n_bins):
        lo = edges[i]
        hi = edges[i + 1]
        if i == n_bins - 1:
            mask = (sig >= lo) & (sig <= hi)
        else:
            mask = (sig >= lo) & (sig < hi)
        if not np.any(mask):
            continue
        weight = float(np.sum(mask)) / total
        ece += weight * abs(float(np.mean(sig[mask])) - float(np.mean(err[mask])))
    return float(ece)


@dataclass
class GlobalScaleCalibrator:
    """Calibrate uncertainty with one scalar multiplier.

    If predicted sigma is systematically too small or too large, a global scale
    can reduce mismatch while remaining transparent and easy to audit.
    """

    scale: float = 1.0

    def fit(self, abs_error: ArrayLike, sigma: ArrayLike) -> "GlobalScaleCalibrator":
        err = _as_1d(abs_error, "abs_error")
        sig = np.maximum(_as_1d(sigma, "sigma"), 1e-12)
        if err.shape != sig.shape:
            raise ValueError("abs_error and sigma must have the same shape.")
        self.scale = float(np.median(err / sig))
        if not np.isfinite(self.scale) or self.scale <= 0:
            self.scale = 1.0
        return self

    def transform(self, sigma: ArrayLike) -> np.ndarray:
        sig = np.maximum(_as_1d(sigma, "sigma"), 1e-12)
        return self.scale * sig


@dataclass
class QuantileBinCalibrator:
    """Piecewise uncertainty calibrator based on sigma quantile bins."""

    n_bins: int = 10
    edges_: np.ndarray | None = None
    scales_: np.ndarray | None = None

    def fit(self, abs_error: ArrayLike, sigma: ArrayLike) -> "QuantileBinCalibrator":
        err = _as_1d(abs_error, "abs_error")
        sig = np.maximum(_as_1d(sigma, "sigma"), 1e-12)
        if err.shape != sig.shape:
            raise ValueError("abs_error and sigma must have the same shape.")
        if self.n_bins < 1:
            raise ValueError("n_bins must be >= 1.")

        self.edges_ = np.quantile(sig, np.linspace(0.0, 1.0, self.n_bins + 1))
        scales: list[float] = []
        for i in range(self.n_bins):
            lo = self.edges_[i]
            hi = self.edges_[i + 1]
            if i == self.n_bins - 1:
                mask = (sig >= lo) & (sig <= hi)
            else:
                mask = (sig >= lo) & (sig < hi)
            if not np.any(mask):
                scales.append(1.0)
                continue
            local_scale = float(np.median(err[mask] / sig[mask]))
            if not np.isfinite(local_scale) or local_scale <= 0:
                local_scale = 1.0
            scales.append(local_scale)
        self.scales_ = np.asarray(scales, dtype=float)
        return self

    def transform(self, sigma: ArrayLike) -> np.ndarray:
        if self.edges_ is None or self.scales_ is None:
            raise RuntimeError("QuantileBinCalibrator must be fitted before transform().")
        sig = np.maximum(_as_1d(sigma, "sigma"), 1e-12)
        calibrated = np.empty_like(sig, dtype=float)
        for idx, value in enumerate(sig):
            bin_idx = int(np.searchsorted(self.edges_[1:-1], value, side="right"))
            calibrated[idx] = value * self.scales_[bin_idx]
        return calibrated


def evaluate_calibration(prediction: ArrayLike, target: ArrayLike, sigma: ArrayLike, n_bins: int = 10) -> CalibrationReport:
    err = absolute_error(prediction, target)
    sig = np.maximum(_as_1d(sigma, "sigma"), 1e-12)
    if err.shape != sig.shape:
        raise ValueError("sigma must have the same shape as prediction and target.")

    return CalibrationReport(
        n=int(err.size),
        mae=float(np.mean(err)),
        pearson_uncertainty_error=safe_corrcoef(sig, err),
        spearman_uncertainty_error=spearman_corr(sig, err),
        ece_abs_error=ece_abs_error(err, sig, n_bins=n_bins),
        coverage_1sigma=coverage(err, sig, 1.0),
        coverage_2sigma=coverage(err, sig, 2.0),
        coverage_3sigma=coverage(err, sig, 3.0),
        mean_sigma=float(np.mean(sig)),
        mean_abs_error=float(np.mean(err)),
    )
