"""
Contribution 11: VLM Navigation Agent
======================================
Uses a Vision-Language Model (VLM) as a high-level semantic planner.
The VLM interprets camera frames, identifies semantic regions (room, corridor,
obstacle type) and generates natural-language goals that are translated into
metric waypoints for the downstream A* planner.

Research Question (RQ-VLM): Can a foundation VLM replace hand-crafted
semantic labelling and improve goal-specification in unknown environments?

Author: DynNav Project
"""

from __future__ import annotations

import base64
import json
import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SemanticGoal:
    """A goal produced by the VLM planner."""
    description: str               # e.g. "navigate to the exit door on the left"
    region_label: str              # e.g. "corridor", "doorway", "open_space"
    confidence: float              # VLM confidence in [0, 1]
    pixel_hint: Optional[tuple[int, int]] = None   # (u, v) pixel of region centroid
    metric_waypoint: Optional[tuple[float, float]] = None  # (x, y) in map frame


@dataclass
class VLMPlannerConfig:
    model_name: str = "llava-1.6"          # or "gpt-4-vision-preview"
    api_endpoint: str = "http://localhost:11434/api/chat"  # Ollama default
    confidence_threshold: float = 0.55
    max_retries: int = 3
    image_resize: tuple[int, int] = (640, 480)
    prompt_template: str = (
        "You are a robot navigation assistant. "
        "Analyse the image and identify: "
        "(1) the main navigable regions, "
        "(2) any obstacles or hazards, "
        "(3) the best next waypoint direction. "
        "Reply ONLY with JSON: "
        '{"region": "<label>", "goal": "<short instruction>", '
        '"confidence": <0-1>, "pixel_u": <int>, "pixel_v": <int>}'
    )
    system_prompt: str = "You are an expert mobile-robot navigation assistant."


# ---------------------------------------------------------------------------
# VLM interface (provider-agnostic)
# ---------------------------------------------------------------------------

class VLMNavigationPlanner:
    """
    Sends camera frames to a VLM and converts semantic goals into metric
    waypoints compatible with DynNav's existing A* backend.

    Supports:
        - Local Ollama (LLaVA, BakLLaVA)
        - OpenAI GPT-4V (set api_endpoint accordingly)
        - Any OpenAI-compatible server
    """

    def __init__(self, config: VLMPlannerConfig | None = None,
                 depth_scale: float = 1.0):
        self.cfg = config or VLMPlannerConfig()
        self.depth_scale = depth_scale   # metres per depth unit
        self._session_goals: list[SemanticGoal] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan(self, rgb_frame: np.ndarray,
             depth_frame: Optional[np.ndarray] = None,
             current_pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
             ) -> Optional[SemanticGoal]:
        """
        Main entry point. Feed an RGB (H×W×3 uint8) frame, get a SemanticGoal.
        """
        # VLM output is untrusted. Never use an invalid pixel, pose or depth
        # as a physical waypoint. Reject before any model/network request.
        if not isinstance(rgb_frame,np.ndarray) or rgb_frame.ndim!=3 or rgb_frame.shape[2]!=3 or rgb_frame.dtype!=np.uint8:
            logger.warning("Rejected non-RGB uint8 input frame")
            return None
        if depth_frame is not None and (not isinstance(depth_frame,np.ndarray)
                or depth_frame.ndim!=2 or depth_frame.shape!=rgb_frame.shape[:2]):
            logger.warning("Rejected incompatible depth frame")
            return None
        if len(current_pose)!=3 or not all(math.isfinite(float(v)) for v in current_pose):
            logger.warning("Rejected nonfinite camera/robot pose")
            return None
        encoded = self._encode_frame(rgb_frame)
        raw = self._query_vlm(encoded)
        if raw is None:
            return None

        goal = self._parse_response(raw)
        if goal is None or not math.isfinite(goal.confidence) or goal.confidence < self.cfg.confidence_threshold:
            logger.warning("VLM goal missing/invalid confidence: %s", goal)
            return None
        if goal.pixel_hint is not None:
            u,v=goal.pixel_hint
            height,width=rgb_frame.shape[:2]
            if not (0<=u<width and 0<=v<height):
                logger.warning("Rejected out-of-frame VLM pixel hint %s",goal.pixel_hint)
                return None

        if depth_frame is not None:
            if goal.pixel_hint is None:
                logger.warning("Depth-aware goal has no grounded pixel hint")
                return None
            waypoint=self._pixel_to_metric(goal.pixel_hint,depth_frame,current_pose)
            if waypoint is None:
                logger.warning("Unusable depth for VLM waypoint; fail closed")
                return None
            goal.metric_waypoint=waypoint

        self._session_goals.append(goal)
        logger.info("VLM goal accepted: %s (conf=%.2f)", goal.description, goal.confidence)
        return goal

    def session_summary(self) -> dict:
        """Return stats on goals produced this session."""
        if not self._session_goals:
            return {"total": 0}
        confs = [g.confidence for g in self._session_goals]
        labels = [g.region_label for g in self._session_goals]
        return {
            "total": len(self._session_goals),
            "mean_confidence": float(np.mean(confs)),
            "region_distribution": {
                lbl: labels.count(lbl) for lbl in set(labels)
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _encode_frame(self, frame: np.ndarray) -> str:
        """Base64-encode an RGB frame for transmission to the VLM API."""
        try:
            from PIL import Image
            import io
            img = Image.fromarray(frame).resize(self.cfg.image_resize)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except ImportError:
            # Fallback: raw numpy bytes
            return base64.b64encode(frame.tobytes()).decode("utf-8")

    def _query_vlm(self, encoded_image: str) -> Optional[str]:
        """Send request to VLM endpoint; returns raw text response or None."""
        import urllib.request, urllib.error

        payload = {
            "model": self.cfg.model_name,
            "messages": [
                {"role": "system", "content": self.cfg.system_prompt},
                {
                    "role": "user",
                    "content": self.cfg.prompt_template,
                    "images": [encoded_image],
                },
            ],
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")

        for attempt in range(self.cfg.max_retries):
            try:
                req = urllib.request.Request(
                    self.cfg.api_endpoint,
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    # Support both Ollama and OpenAI response shapes
                    if "message" in result:
                        return result["message"]["content"]
                    if "choices" in result:
                        return result["choices"][0]["message"]["content"]
            except (urllib.error.URLError, TimeoutError) as e:
                logger.warning("VLM attempt %d failed: %s", attempt + 1, e)

        return None

    def _parse_response(self, raw: str) -> Optional[SemanticGoal]:
        """Parse JSON from the VLM response."""
        try:
            text=raw.strip()
            if text.startswith("```"):
                parts=text.splitlines()
                if len(parts)<3 or not parts[-1].strip().startswith("```"):
                    raise ValueError("Malformed fenced VLM JSON")
                text="\n".join(parts[1:-1]).strip()
            data=json.loads(text)
            if not isinstance(data,dict):
                raise ValueError("VLM JSON response is not an object")
            confidence=float(data.get("confidence",0.))
            if not math.isfinite(confidence) or not 0<=confidence<=1:
                raise ValueError("VLM confidence is nonfinite or out of [0,1]")
            goal=str(data.get("goal","")).strip()
            region=str(data.get("region","")).strip()
            if not goal or not region or region.lower()=="unknown":
                raise ValueError("VLM region or goal missing")
            if ("pixel_u" in data) != ("pixel_v" in data):
                raise ValueError("Incomplete VLM pixel coordinate pair")
            pixels=(int(data["pixel_u"]),int(data["pixel_v"])) if "pixel_u" in data else None
            return SemanticGoal(description=goal,region_label=region,
                                confidence=confidence,pixel_hint=pixels)
        except (json.JSONDecodeError,KeyError,ValueError,TypeError,OverflowError) as e:
            logger.error("Failed to parse VLM response: %s | raw=%s", e, raw[:200])
            return None

    def _pixel_to_metric(self, pixel: tuple[int, int],
                         depth: np.ndarray,
                         pose: tuple[float, float, float]) -> tuple[float, float]:
        """
        Back-project a pixel (u, v) using the depth map to a (x, y) world point.
        Uses a simple pinhole model; replace with full camera intrinsics for accuracy.
        """
        u, v = pixel
        h, w = depth.shape[:2]
        if not (0<=u<w and 0<=v<h) or not math.isfinite(self.depth_scale) or self.depth_scale<=0:
            return None
        fx = fy = max(w, h)   # approximate focal length; NOT a calibrated camera
        cx, cy = w / 2, h / 2
        d = float(depth[v,u])*self.depth_scale
        if not math.isfinite(d) or d<0.05:
            logger.warning("Invalid/nonfinite/too-small depth at %s: %s",pixel,d)
            return None

        # Camera-frame 3-D point
        x_cam = (u - cx) / fx * d
        z_cam = d

        # Rotate into world frame using yaw from pose
        yaw = pose[2]
        cos_y, sin_y = np.cos(yaw), np.sin(yaw)
        x_world = pose[0] + cos_y * z_cam - sin_y * x_cam
        y_world = pose[1] + sin_y * z_cam + cos_y * x_cam

        return (float(x_world), float(y_world))
