"""Cyber-physical security research primitives for DynNav."""

from .detectors import CUSUMDetector, DetectorConfig, EWMADetector, NISDetector, create_detector
from .events import AttributionResult, DetectorResult, ResidualEvent, TrustState
from .statistics import chi_square_quantile, chi_square_quantile_fallback, mahalanobis_squared, validate_covariance
from .trust import SourceTrustEstimator, TrustConfig

__all__ = [
    "AttributionResult",
    "CUSUMDetector",
    "DetectorConfig",
    "DetectorResult",
    "EWMADetector",
    "NISDetector",
    "ResidualEvent",
    "SourceTrustEstimator",
    "TrustConfig",
    "TrustState",
    "chi_square_quantile",
    "chi_square_quantile_fallback",
    "create_detector",
    "mahalanobis_squared",
    "validate_covariance",
]
