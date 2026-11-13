"""
Contribution 20: Multimodal Failure Explainer
=============================================
After a navigation failure (collision, timeout, irreversibility violation),
automatically generates a structured failure report combining:
    - VLM-based scene description of the failure frame
    - Causal attribution from Contribution 14 (SCM)
    - STL robustness trace from Contribution 18
    - Suggested corrective actions

Output formats: JSON, Markdown, or plain text.

Research Question (RQ-Explain): Does automated failure explanation
reduce human operator debugging time and improve replanning quality?
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class FailureType(Enum):
    COLLISION = "collision"
    TIMEOUT = "timeout"
    IRREVERSIBLE = "irreversible_state"
    GOAL_MISSED = "goal_missed"
    SENSOR_FAULT = "sensor_fault"
    SAFETY_VIOLATION = "safety_violation"


@dataclass
class FailureEvent:
    failure_type: FailureType
    timestamp: float
    robot_pos: tuple[float, float]
    robot_vel: tuple[float, float]
    frame: Optional[np.ndarray] = None          # RGB image at failure
    state_trajectory: Optional[np.ndarray] = None  # (T, state_dim)
    stl_robustness: Optional[dict] = None
    sensor_readings: Optional[dict] = None


@dataclass
class FailureReport:
    failure_type: str
    timestamp: float
    robot_pos: tuple
    scene_description: str
    root_causes: list[tuple[str, float]]
    stl_summary: str
    corrective_actions: list[str]
    confidence: float

    def to_markdown(self) -> str:
        lines = [
            f"# Failure Report — {self.failure_type}",
            f"**Time:** {self.timestamp:.2f}s | **Position:** {self.robot_pos}",
            "**Confidence:** unavailable (no calibrated confidence model)",
            "",
            "## Scene Description",
            self.scene_description,
            "",
            "## Root Causes",
        ]
        for name, score in self.root_causes:
            lines.append(f"- `{name}`: causal contribution = {score:.3f}")
        lines += [
            "",
            "## Safety Monitor Summary",
            self.stl_summary,
            "",
            "## Suggested Corrective Actions",
        ]
        for i, action in enumerate(self.corrective_actions, 1):
            lines.append(f"{i}. {action}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "failure_type": self.failure_type,
            "timestamp": self.timestamp,
            "robot_pos": list(self.robot_pos),
            "scene_description": self.scene_description,
            "root_causes": [{"name": n, "score": s} for n, s in self.root_causes],
            "stl_summary": self.stl_summary,
            "corrective_actions": self.corrective_actions,
            "confidence": self.confidence,
            "confidence_status": "unavailable_uncalibrated",
            "causal_attribution_status": "unavailable_no_episode_grounded_model",
        }


class MultimodalFailureExplainer:
    """
    Combines VLM scene analysis, causal attribution, and STL monitoring
    to produce human-readable failure reports.
    """

    CORRECTIVE_ACTIONS = {
        FailureType.COLLISION: [
            "Increase safety radius in CBF filter (Contribution 18)",
            "Reduce velocity near high-risk zones",
            "Re-run diffusion occupancy predictor (Contribution 12)",
            "Check sensor calibration for blind spots",
        ],
        FailureType.TIMEOUT: [
            "Increase planning horizon or switch to greedy planner",
            "Check for deadlock in topological map (Contribution 17)",
            "Reduce replanning frequency to save computation",
        ],
        FailureType.IRREVERSIBLE: [
            "Tighten returnability constraints (Contribution 04)",
            "Enable mental rollout screening (Contribution 13)",
            "Add U-turn manoeuvre to action space",
        ],
        FailureType.SENSOR_FAULT: [
            "Activate IDS alert (Contribution 08)",
            "Switch to dead-reckoning until sensor recovery",
            "Cross-validate with neuromorphic event camera (Contribution 15)",
        ],
        FailureType.SAFETY_VIOLATION: [
            "Tighten STL specification margin",
            "Increase CBF alpha gain for faster response",
            "Alert human operator for manual intervention",
        ],
        FailureType.GOAL_MISSED: [
            "Re-ground semantic goal via VLM (Contribution 11)",
            "Update topological map with new zone boundaries",
        ],
    }

    def __init__(self, use_vlm: bool = False, use_causal: bool = True):
        self.use_vlm = use_vlm
        self.use_causal = use_causal

    def explain(self, event: FailureEvent) -> FailureReport:
        scene_desc = self._describe_scene(event)
        root_causes = self._attribute_causes(event)
        stl_summary = self._summarise_stl(event)
        actions = self.CORRECTIVE_ACTIONS.get(event.failure_type, ["Investigate manually"])

        # No fitted/validated confidence model or episode causal model is wired
        # here. A formatted description is not probabilistic causal evidence.
        confidence = 0.0

        report = FailureReport(
            failure_type=event.failure_type.value,
            timestamp=event.timestamp,
            robot_pos=event.robot_pos,
            scene_description=scene_desc,
            root_causes=root_causes,
            stl_summary=stl_summary,
            corrective_actions=actions,
            confidence=round(confidence, 3),
        )
        logger.info("Failure report generated: type=%s causes=%d",
                    event.failure_type.value, len(root_causes))
        return report

    def _describe_scene(self, event: FailureEvent) -> str:
        if event.frame is not None and self.use_vlm:
            return self._vlm_describe(event.frame, event.failure_type)
        # Rule-based fallback
        vx, vy = event.robot_vel
        speed = np.sqrt(vx**2 + vy**2)
        desc = (
            f"Robot at position ({event.robot_pos[0]:.2f}, {event.robot_pos[1]:.2f}) "
            f"travelling at {speed:.2f} m/s experienced a {event.failure_type.value}."
        )
        if event.sensor_readings:
            min_d = event.sensor_readings.get("min_obstacle_dist", None)
            if min_d is not None:
                desc += f" Nearest obstacle was {min_d:.2f} m away."
        return desc

    def _vlm_describe(self, frame: np.ndarray,
                       failure_type: FailureType) -> str:
        """Fail closed until an actual visual analysis provider is integrated."""
        return "Scene analysis unavailable."

    def _attribute_causes(self, event: FailureEvent
                           ) -> list[tuple[str, float]]:
        """No episode-grounded causal model is integrated; never invent scores."""
        return []

    def _summarise_stl(self, event: FailureEvent) -> str:
        if not event.stl_robustness:
            return "No STL data recorded for this episode."
        violations = {k: v for k, v in event.stl_robustness.items() if v < 0}
        if not violations:
            return "All STL specifications were satisfied at failure time."
        parts = [f"'{k}' (ρ={v:.3f})" for k, v in violations.items()]
        return f"STL violations: {', '.join(parts)}."
