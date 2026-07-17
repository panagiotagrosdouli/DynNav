"""Validated statistical primitives for cyber-physical residual monitoring."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np


@dataclass(frozen=True)
class CovarianceDiagnostics:
    regularized: bool
    used_pseudoinverse: bool
    condition_number: float
    min_eigenvalue: float


def chi_square_quantile(alpha: float, dof: int) -> float:
    """Return the upper-tail chi-square threshold, using SciPy when available."""
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    if dof <= 0:
        raise ValueError("dof must be positive")
    try:
        from scipy.stats import chi2

        return float(chi2.isf(alpha, dof))
    except ImportError:
        return chi_square_quantile_fallback(alpha, dof)


def chi_square_quantile_fallback(alpha: float, dof: int) -> float:
    """Wilson-Hilferty fallback; retained only for environments without SciPy."""
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    if dof <= 0:
        raise ValueError("dof must be positive")
    z = NormalDist().inv_cdf(1.0 - alpha)
    k = float(dof)
    transformed = 1.0 - 2.0 / (9.0 * k) + z * math.sqrt(2.0 / (9.0 * k))
    return max(0.0, k * transformed**3)


def validate_covariance(
    covariance: np.ndarray,
    dimension: int,
    *,
    regularization: float = 1e-9,
    condition_limit: float = 1e12,
) -> tuple[np.ndarray, CovarianceDiagnostics]:
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape != (dimension, dimension):
        raise ValueError(f"covariance must have shape {(dimension, dimension)}, got {matrix.shape}")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("covariance contains non-finite values")
    if not np.allclose(matrix, matrix.T, rtol=1e-8, atol=1e-10):
        raise ValueError("covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(matrix)
    minimum = float(eigenvalues.min())
    if minimum < -1e-10:
        raise ValueError(f"covariance is not positive semidefinite (min eigenvalue={minimum:.3e})")
    regularized = minimum <= 0.0
    stable = matrix + (regularization * np.eye(dimension) if regularized else 0.0)
    condition = float(np.linalg.cond(stable))
    use_pinv = not np.isfinite(condition) or condition > condition_limit
    return stable, CovarianceDiagnostics(regularized, use_pinv, condition, minimum)


def mahalanobis_squared(
    innovation: np.ndarray,
    covariance: np.ndarray,
    *,
    regularization: float = 1e-9,
    condition_limit: float = 1e12,
) -> tuple[float, CovarianceDiagnostics]:
    vector = np.asarray(innovation, dtype=float).reshape(-1)
    if vector.size == 0 or not np.all(np.isfinite(vector)):
        raise ValueError("innovation must be a non-empty finite vector")
    stable, diagnostics = validate_covariance(
        covariance,
        vector.size,
        regularization=regularization,
        condition_limit=condition_limit,
    )
    solution = np.linalg.pinv(stable) @ vector if diagnostics.used_pseudoinverse else np.linalg.solve(stable, vector)
    value = float(vector.T @ solution)
    return max(0.0, value), diagnostics
