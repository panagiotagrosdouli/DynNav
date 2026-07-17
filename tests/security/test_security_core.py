from __future__ import annotations

import numpy as np
import pytest

from dynnav.security import (
    DetectorResult,
    NISDetector,
    ResidualEvent,
    SourceTrustEstimator,
    TrustConfig,
    chi_square_quantile,
    chi_square_quantile_fallback,
    mahalanobis_squared,
)


def event(value: float, timestamp: float = 0.0) -> ResidualEvent:
    return ResidualEvent(
        source_id="gps",
        measurement=np.array([value]),
        prediction=np.zeros(1),
        innovation=np.array([value]),
        covariance=np.eye(1),
        timestamp=timestamp,
    )


def result(*, flagged: bool, confidence: float, timestamp: float) -> DetectorResult:
    return DetectorResult(
        statistic=10.0 if flagged else 0.1,
        threshold=3.0,
        flagged=flagged,
        triggered=flagged,
        confidence=confidence,
        latency=0,
        detector_name="test",
        source_id="gps",
        timestamp=timestamp,
    )


def test_mahalanobis_squared() -> None:
    value, diagnostics = mahalanobis_squared(np.array([2.0]), np.array([[4.0]]))
    assert value == pytest.approx(1.0)
    assert not diagnostics.regularized


def test_singular_covariance_is_diagnosed() -> None:
    value, diagnostics = mahalanobis_squared(np.array([1.0, 0.0]), np.diag([1.0, 0.0]))
    assert np.isfinite(value)
    assert diagnostics.regularized


def test_malformed_covariance_is_rejected() -> None:
    with pytest.raises(ValueError, match="symmetric"):
        mahalanobis_squared(np.ones(2), np.array([[1.0, 2.0], [0.0, 1.0]]))


@pytest.mark.parametrize("dof", [1, 2, 5, 10, 30])
@pytest.mark.parametrize("alpha", [0.1, 0.05, 0.01])
def test_fallback_quantile_has_bounded_relative_error(dof: int, alpha: float) -> None:
    reference = chi_square_quantile(alpha, dof)
    fallback = chi_square_quantile_fallback(alpha, dof)
    assert abs(fallback - reference) / reference < 0.08


def test_consecutive_trigger() -> None:
    detector = NISDetector()
    detector.config = detector.config.__class__(warmup=0, consecutive=3)
    outputs = [detector.update(event(4.0, float(index))) for index in range(3)]
    assert not outputs[1].triggered
    assert outputs[2].triggered


def test_trust_loss_is_faster_than_recovery() -> None:
    estimator = SourceTrustEstimator(
        "gps",
        TrustConfig(loss_rate=0.5, recovery_rate=0.1, recovery_samples=3, warmup=0),
    )
    degraded = estimator.update(result(flagged=True, confidence=1.0, timestamp=1.0))
    after_one_normal = estimator.update(result(flagged=False, confidence=0.0, timestamp=2.0))
    assert degraded.filtered_trust < 0.75
    assert after_one_normal.filtered_trust == degraded.filtered_trust
    recovered = after_one_normal
    for step in range(3, 20):
        recovered = estimator.update(result(flagged=False, confidence=0.0, timestamp=float(step)))
    assert recovered.filtered_trust > degraded.filtered_trust
    assert recovered.filtered_trust < 1.0
