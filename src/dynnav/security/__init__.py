"""Cyber-physical security research primitives for DynNav."""

from .attack_graph import AttackCampaign, CampaignCorrelator, CampaignLink, SecurityAlert
from .attribution import AttributionEvidence, attribute_anomaly
from .detectors import CUSUMDetector, DetectorConfig, EWMADetector, NISDetector, create_detector
from .events import AttributionResult, DetectorResult, ResidualEvent, TrustState
from .fusion import FusedTrust, FusionMethod, fuse_trust
from .mitigation import (
    MitigationAction,
    MitigationDecision,
    NavigationContext,
    choose_mitigation,
    security_risk,
)
from .sensor_profiles import (
    SensorKind,
    SensorSecurityProfile,
    available_sensor_profiles,
    create_sensor_detector,
    get_sensor_profile,
)
from .statistics import chi_square_quantile, chi_square_quantile_fallback, mahalanobis_squared, validate_covariance
from .temporal import SecurityState, SecurityStateMachine, StateMachineConfig, StateTransition
from .trust import SourceTrustEstimator, TrustConfig

__all__ = [
    "AttackCampaign",
    "AttributionEvidence",
    "AttributionResult",
    "CUSUMDetector",
    "CampaignCorrelator",
    "CampaignLink",
    "DetectorConfig",
    "DetectorResult",
    "EWMADetector",
    "FusedTrust",
    "FusionMethod",
    "MitigationAction",
    "MitigationDecision",
    "NISDetector",
    "NavigationContext",
    "ResidualEvent",
    "SecurityAlert",
    "SecurityState",
    "SecurityStateMachine",
    "SensorKind",
    "SensorSecurityProfile",
    "SourceTrustEstimator",
    "StateMachineConfig",
    "StateTransition",
    "TrustConfig",
    "TrustState",
    "attribute_anomaly",
    "available_sensor_profiles",
    "chi_square_quantile",
    "chi_square_quantile_fallback",
    "choose_mitigation",
    "create_detector",
    "create_sensor_detector",
    "fuse_trust",
    "get_sensor_profile",
    "mahalanobis_squared",
    "security_risk",
    "validate_covariance",
]
