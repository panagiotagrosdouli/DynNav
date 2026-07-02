"""Attack-impact evaluation utilities for Contribution 25.

The base simulator generates attacks. This evaluator measures whether attacks are
visible to a simple detector and how much they degrade navigation-relevant
signals.

Metrics:
- attack detection precision / recall / F1,
- point-cloud geometry impact,
- odometry drift error,
- minimum-distance degradation,
- severity score,
- mitigation recommendation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from adversarial_attacks import AttackConfig, GradientAttacker, LiDARAttacker, OdometrySpoofer


@dataclass(frozen=True)
class AttackImpactResult:
    attack_name: str
    detected: bool
    true_attack: bool
    severity_score: float
    min_distance_before: float
    min_distance_after: float
    min_distance_degradation: float
    geometry_change: float
    odometry_error_m: float
    mitigation: str

    def to_dict(self) -> dict[str, float | bool | str]:
        return asdict(self)


def synthetic_observation(seed: int, dim: int = 16) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.clip(rng.normal(0.5, 0.18, dim), 0.0, 1.0)


def synthetic_point_cloud(seed: int, n: int = 320) -> np.ndarray:
    rng = np.random.default_rng(seed)
    wall_x = rng.uniform(1.0, 5.0, n // 2)
    wall = np.column_stack([wall_x, np.full(n // 2, 1.2), rng.normal(0.2, 0.05, n // 2)])
    clutter = rng.normal(loc=(2.8, -0.6, 0.25), scale=(0.35, 0.25, 0.06), size=(n // 2, 3))
    return np.vstack([wall, clutter])


def min_xy_distance(point_cloud: np.ndarray, robot_pos: np.ndarray | None = None) -> float:
    robot = np.asarray(robot_pos if robot_pos is not None else np.zeros(3), dtype=float)
    return float(np.min(np.linalg.norm(point_cloud[:, :2] - robot[:2], axis=1)))


def geometry_change(original: np.ndarray, attacked: np.ndarray) -> float:
    count_change = abs(len(attacked) - len(original)) / max(1, len(original))
    before_centroid = np.mean(original[:, :2], axis=0)
    after_centroid = np.mean(attacked[:, :2], axis=0)
    centroid_shift = float(np.linalg.norm(after_centroid - before_centroid))
    return float(count_change + centroid_shift)


def simple_attack_detector(
    *,
    geometry_delta: float,
    odom_error: float,
    loss_increase: float,
    thresholds: tuple[float, float, float] = (0.20, 0.35, 0.20),
) -> bool:
    geom_thr, odom_thr, loss_thr = thresholds
    return bool(geometry_delta > geom_thr or odom_error > odom_thr or loss_increase > loss_thr)


def mitigation_from_severity(severity: float) -> str:
    if severity >= 0.75:
        return "emergency_stop_and_request_operator"
    if severity >= 0.45:
        return "safe_mode_and_sensor_cross_check"
    if severity >= 0.20:
        return "increase_trust_monitoring"
    return "continue_with_watch"


def evaluate_lidar_attack(attack_name: str, cfg: AttackConfig, seed: int = 25) -> AttackImpactResult:
    pc = synthetic_point_cloud(seed)
    attacker = LiDARAttacker(cfg)
    if attack_name == "lidar_spoof_add":
        attacked = attacker.spoof_add(pc, np.zeros(3))
    elif attack_name == "lidar_spoof_remove":
        attacked = attacker.spoof_remove(pc, target_region=np.asarray([2.8, -0.6, 0.25]))
    elif attack_name == "sensor_blind":
        attacked = attacker.sensor_blind(pc)
    else:
        raise ValueError(f"Unsupported LiDAR attack {attack_name}")

    before = min_xy_distance(pc)
    after = min_xy_distance(attacked) if len(attacked) else float("inf")
    geom = geometry_change(pc, attacked)
    degradation = float(max(0.0, before - after) + 0.25 * geom)
    severity = float(np.clip(degradation, 0.0, 1.0))
    detected = simple_attack_detector(geometry_delta=geom, odom_error=0.0, loss_increase=0.0)
    return AttackImpactResult(
        attack_name=attack_name,
        detected=detected,
        true_attack=True,
        severity_score=severity,
        min_distance_before=before,
        min_distance_after=after,
        min_distance_degradation=float(before - after),
        geometry_change=geom,
        odometry_error_m=0.0,
        mitigation=mitigation_from_severity(severity),
    )


def evaluate_odometry_attack(cfg: AttackConfig, seed: int = 25) -> AttackImpactResult:
    spoofer = OdometrySpoofer(cfg)
    spoofer.activate()
    true_odom = np.asarray([2.0, 1.0, 0.0])
    corrupted = true_odom.copy()
    for _ in range(80):
        corrupted = spoofer.corrupt(true_odom)
    odom_error = float(np.linalg.norm(corrupted[:2] - true_odom[:2]))
    severity = float(np.clip(odom_error / 1.2, 0.0, 1.0))
    detected = simple_attack_detector(geometry_delta=0.0, odom_error=odom_error, loss_increase=0.0)
    spoofer.deactivate()
    return AttackImpactResult(
        attack_name="odom_drift",
        detected=detected,
        true_attack=True,
        severity_score=severity,
        min_distance_before=0.0,
        min_distance_after=0.0,
        min_distance_degradation=0.0,
        geometry_change=0.0,
        odometry_error_m=odom_error,
        mitigation=mitigation_from_severity(severity),
    )


def evaluate_gradient_attack(attack_name: str, cfg: AttackConfig, seed: int = 25) -> AttackImpactResult:
    obs = synthetic_observation(seed)
    attacker = GradientAttacker(cfg)
    loss_fn = lambda x: float(np.mean((x - 0.95) ** 2))
    if attack_name == "fgsm":
        adv = attacker.fgsm(obs, loss_fn)
    elif attack_name == "pgd":
        adv = attacker.pgd(obs, loss_fn)
    else:
        raise ValueError(f"Unsupported gradient attack {attack_name}")
    loss_increase = float(loss_fn(adv) - loss_fn(obs))
    severity = float(np.clip(abs(loss_increase) * 3.0, 0.0, 1.0))
    detected = simple_attack_detector(geometry_delta=0.0, odom_error=0.0, loss_increase=abs(loss_increase))
    return AttackImpactResult(
        attack_name=attack_name,
        detected=detected,
        true_attack=True,
        severity_score=severity,
        min_distance_before=0.0,
        min_distance_after=0.0,
        min_distance_degradation=0.0,
        geometry_change=0.0,
        odometry_error_m=0.0,
        mitigation=mitigation_from_severity(severity),
    )


def summarize_detection(results: list[AttackImpactResult]) -> dict[str, float | int]:
    if not results:
        raise ValueError("results must not be empty")
    tp = sum(r.detected and r.true_attack for r in results)
    fp = sum(r.detected and not r.true_attack for r in results)
    fn = sum((not r.detected) and r.true_attack for r in results)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {
        "n_cases": len(results),
        "detection_precision": float(precision),
        "detection_recall": float(recall),
        "detection_f1": float(f1),
        "mean_severity": float(np.mean([r.severity_score for r in results])),
    }
