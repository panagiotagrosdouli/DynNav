"""DynNav research package.

The package contains deterministic research prototypes for risk-aware planning,
dynamic rerouting, uncertainty propagation, recoverability analysis, monitoring,
and benchmarking. Components are intentionally lightweight so they can run in CI
without ROS 2; ROS integration points are isolated in :mod:`dynnav.ros2`.
"""

from dynnav.config import DynNavConfig
from dynnav.core import GridMap, Pose, Trajectory

__all__ = ["DynNavConfig", "GridMap", "Pose", "Trajectory"]
