"""
core/adversarial.py
=====================
Reproduces DynNav Contribution 25's threat model (FGSM/PGD perturbations +
LiDAR spoofing) at the occupancy-grid level used by this benchmark.
Since planners here consume occupancy/uncertainty *grids* rather than raw
sensor tensors, FGSM/PGD are realized as their natural grid-level analogue:
a single-step (FGSM) vs. iterative-projected (PGD) adversarial perturbation
of the *observed* occupancy field, bounded by an L_inf budget epsilon,
designed to maximize planner risk-miscalibration (push occupied cells to
look free, or vice versa) -- the same attack objective used in Contribution 25.
"""
from __future__ import annotations
import numpy as np


def fgsm_attack(occ_obs: np.ndarray, occ_gt: np.ndarray, epsilon: float, rng) -> np.ndarray:
    """One-step gradient-sign-style attack: push observed occupancy away from truth."""
    sign = np.sign(occ_gt - occ_obs + rng.normal(0, 1e-3, size=occ_obs.shape))
    perturbed = occ_obs - epsilon * sign  # push toward wrong label
    return np.clip(perturbed, 0, 1).astype(np.float32)


def pgd_attack(occ_obs: np.ndarray, occ_gt: np.ndarray, epsilon: float, rng,
               steps: int = 5, step_size: float = None) -> np.ndarray:
    """Iterative projected attack: stronger, budget-constrained version of FGSM."""
    step_size = step_size or (epsilon / steps) * 1.5
    x = occ_obs.copy()
    for _ in range(steps):
        sign = np.sign(occ_gt - x + rng.normal(0, 1e-3, size=x.shape))
        x = x - step_size * sign
        x = np.clip(x, occ_obs - epsilon, occ_obs + epsilon)  # project to L_inf ball
        x = np.clip(x, 0, 1)
    return x.astype(np.float32)


def sensor_spoofing_attack(occ_obs: np.ndarray, epsilon: float, rng, n_patches: int = 4) -> np.ndarray:
    """Localized spoofed-LiDAR-return patches (phantom obstacles / cloaked obstacles)."""
    x = occ_obs.copy()
    H, W = x.shape
    for _ in range(n_patches):
        r, c = rng.integers(0, H), rng.integers(0, W)
        r0, r1 = max(0, r - 2), min(H, r + 2)
        c0, c1 = max(0, c - 2), min(W, c + 2)
        direction = rng.choice([-1.0, 1.0])
        x[r0:r1, c0:c1] = np.clip(x[r0:r1, c0:c1] + direction * epsilon, 0, 1)
    return x.astype(np.float32)


ATTACK_FUNCS = {
    "none": lambda occ_obs, occ_gt, eps, rng: occ_obs,
    "fgsm": fgsm_attack,
    "pgd": lambda occ_obs, occ_gt, eps, rng: pgd_attack(occ_obs, occ_gt, eps, rng),
    "spoofing": lambda occ_obs, occ_gt, eps, rng: sensor_spoofing_attack(occ_obs, eps, rng),
}
