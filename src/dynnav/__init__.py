"""DynNav research package.

The package contains deterministic research prototypes for risk-aware planning,
dynamic rerouting, uncertainty propagation, recoverability analysis, monitoring,
and benchmarking. Components are intentionally lightweight so they can run in CI
without ROS 2; ROS integration points are isolated in :mod:`dynnav.ros2`.
"""

from dynnav.config import DynNavConfig
from dynnav.core import (
    GridMap,
    NavigationState,
    PathEvaluation,
    Pose,
    SelfAwarenessScore,
    SelfAwareCostWeights,
    Trajectory,
    estimate_self_awareness,
    expected_information_gain,
    self_aware_path_cost,
)
from dynnav.research_modules import (
    DynNavResearchStack,
    MissionRiskEstimator,
    MissionRiskReport,
    RuntimeMonitor,
    RuntimeObservation,
    SafetyMode,
    SafeModeSupervisor,
    UncertaintyPropagator,
    UncertaintyState,
)

__all__ = [
    "DynNavConfig",
    "DynNavResearchStack",
    "GridMap",
    "MissionRiskEstimator",
    "MissionRiskReport",
    "NavigationState",
    "PathEvaluation",
    "Pose",
    "RuntimeMonitor",
    "RuntimeObservation",
    "SafeModeSupervisor",
    "SafetyMode",
    "SelfAwarenessScore",
    "SelfAwareCostWeights",
    "Trajectory",
    "UncertaintyPropagator",
    "UncertaintyState",
    "estimate_self_awareness",
    "expected_information_gain",
    "self_aware_path_cost",
]
