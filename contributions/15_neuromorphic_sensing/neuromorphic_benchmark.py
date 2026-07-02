"""Neuromorphic sensing benchmark utilities for Contribution 15.

This module evaluates whether event-based obstacle detection offers lower
reaction latency than frame-based detection in simple moving-obstacle sequences.
It is intentionally lightweight and deterministic enough for repository tests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from neuromorphic_sensing import DVSSimulator, DVSSimulatorConfig, SNNObstacleDetector, event_to_time_surface


@dataclass(frozen=True)
class DetectionMetrics:
    method: str
    detected: bool
    detection_time_us: float
    latency_us: float
    false_negative: bool
    n_events: int
    event_rate_per_ms: float
    max_score: float

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


def moving_obstacle_frames(
    n_frames: int = 8,
    height: int = 64,
    width: int = 64,
    obstacle_size: int = 10,
    start_col: int = 4,
    speed_px_per_frame: int = 6,
) -> list[np.ndarray]:
    """Generate a bright square moving horizontally on a dark background."""
    frames: list[np.ndarray] = []
    for t in range(n_frames):
        frame = np.zeros((height, width), dtype=float) + 0.05
        c0 = min(width - obstacle_size - 1, start_col + t * speed_px_per_frame)
        r0 = height // 2 - obstacle_size // 2
        frame[r0:r0 + obstacle_size, c0:c0 + obstacle_size] = 0.95
        frames.append(frame)
    return frames


def frame_based_detection(frame: np.ndarray, threshold: float = 0.5) -> float:
    """Simple frame-based obstacle confidence."""
    return float(np.max(frame) >= threshold)


def evaluate_event_detector(
    frames: list[np.ndarray],
    dt_us: float = 10_000.0,
    detect_threshold: float = 0.05,
) -> DetectionMetrics:
    if not frames:
        raise ValueError("frames must not be empty")
    h, w = frames[0].shape
    sim = DVSSimulator(DVSSimulatorConfig(height=h, width=w, noise_rate=0.0, threshold_pos=0.12, threshold_neg=0.12))
    detector = SNNObstacleDetector(grid_n=4, grid_m=4)
    all_events = []
    first_detection_time = float("inf")
    max_score = 0.0

    for idx, frame in enumerate(frames):
        events = sim.process_frame(frame, dt_us=dt_us)
        all_events.extend(events)
        surface = event_to_time_surface(events, h=h, w=w)
        score = float(np.max(detector.detect(surface)))
        max_score = max(max_score, score)
        if score >= detect_threshold and not np.isfinite(first_detection_time):
            first_detection_time = idx * dt_us

    detected = np.isfinite(first_detection_time)
    total_time_ms = max(1e-9, len(frames) * dt_us / 1000.0)
    return DetectionMetrics(
        method="event_snn",
        detected=bool(detected),
        detection_time_us=float(first_detection_time if detected else -1.0),
        latency_us=float(first_detection_time if detected else len(frames) * dt_us),
        false_negative=not detected,
        n_events=len(all_events),
        event_rate_per_ms=float(len(all_events) / total_time_ms),
        max_score=max_score,
    )


def evaluate_frame_baseline(
    frames: list[np.ndarray],
    dt_us: float = 33_333.0,
    threshold: float = 0.5,
) -> DetectionMetrics:
    if not frames:
        raise ValueError("frames must not be empty")
    first_detection_time = float("inf")
    max_score = 0.0
    for idx, frame in enumerate(frames):
        score = frame_based_detection(frame, threshold=threshold)
        max_score = max(max_score, score)
        if score >= 1.0 and not np.isfinite(first_detection_time):
            first_detection_time = idx * dt_us
    detected = np.isfinite(first_detection_time)
    return DetectionMetrics(
        method="frame_baseline",
        detected=bool(detected),
        detection_time_us=float(first_detection_time if detected else -1.0),
        latency_us=float(first_detection_time if detected else len(frames) * dt_us),
        false_negative=not detected,
        n_events=0,
        event_rate_per_ms=0.0,
        max_score=float(max_score),
    )
