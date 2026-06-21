"""
core/grid_env.py
=================
Grid-world environment generator for the DynNav Trust-Aware CVaR benchmark.

Reuses the modelling philosophy of DynNav's existing contributions:
 - Contribution 03 (Belief-Space & Risk Planning) -> occupancy + uncertainty grids
 - Contribution 12 (Diffusion Occupancy)          -> probabilistic occupancy field
 - Contribution 08/25 (Security/Adversarial)       -> sensor corruption / spoofing
 - Contribution 05 (Safe-Mode)                     -> risk field used for triggers

Each environment is represented as:
    occupancy_gt   : (H,W) float32 ground-truth occupancy in [0,1] (obstacles)
    occupancy_obs  : (H,W) float32 *observed* (noisy/corrupted) occupancy used by planners
    uncertainty    : (H,W) float32 per-cell epistemic uncertainty (sigma)
    dynamic_agents : list[DynamicAgent] moving obstacles with simple intent models
    start, goal    : (row, col) tuples
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple

ENV_TYPES = [
    "static",
    "dynamic",
    "dense",
    "adversarial",
    "sensor_corruption",
    "low_visibility",
]


@dataclass
class DynamicAgent:
    pos: np.ndarray          # (2,) float row,col
    vel: np.ndarray          # (2,) float
    radius: float = 1.2

    def step(self, H, W, rng):
        # simple constant-velocity + small random walk ("intent" = current heading)
        self.pos = self.pos + self.vel + rng.normal(0, 0.05, size=2)
        # bounce off walls
        for d in (0, 1):
            lim = H if d == 0 else W
            if self.pos[d] < 1 or self.pos[d] > lim - 2:
                self.vel[d] *= -1
                self.pos[d] = np.clip(self.pos[d], 1, lim - 2)


@dataclass
class GridEnvironment:
    H: int
    W: int
    occupancy_gt: np.ndarray
    occupancy_obs: np.ndarray
    uncertainty: np.ndarray
    start: Tuple[int, int]
    goal: Tuple[int, int]
    env_type: str
    dynamic_agents: List[DynamicAgent] = field(default_factory=list)
    visibility_mask: np.ndarray = None  # 1 = visible, 0 = occluded/unknown
    seed: int = 0

    def dynamic_occupancy_snapshot(self) -> np.ndarray:
        """Rasterize current dynamic-agent positions onto the ground-truth grid."""
        occ = self.occupancy_gt.copy()
        for a in self.dynamic_agents:
            r, c = int(round(a.pos[0])), int(round(a.pos[1]))
            rad = int(np.ceil(a.radius))
            r0, r1 = max(0, r - rad), min(self.H, r + rad + 1)
            c0, c1 = max(0, c - rad), min(self.W, c + rad + 1)
            occ[r0:r1, c0:c1] = np.maximum(occ[r0:r1, c0:c1], 0.95)
        return occ

    def step_agents(self, rng):
        for a in self.dynamic_agents:
            a.step(self.H, self.W, rng)


def _carve_random_obstacles(H, W, rng, density):
    grid = (rng.random((H, W)) < density).astype(np.float32)
    return grid


def _blur(grid, iters=1):
    """Cheap box-blur to make obstacle boundaries probabilistic instead of binary."""
    out = grid.copy()
    for _ in range(iters):
        pad = np.pad(out, 1, mode="edge")
        out = (
            pad[0:-2, 0:-2] + pad[0:-2, 1:-1] + pad[0:-2, 2:]
            + pad[1:-1, 0:-2] + pad[1:-1, 1:-1] + pad[1:-1, 2:]
            + pad[2:, 0:-2] + pad[2:, 1:-1] + pad[2:, 2:]
        ) / 9.0
    return out


def make_environment(env_type: str, size: int, seed: int,
                      sensor_noise_std: float = 0.05,
                      corruption_strength: float = 0.0,
                      visibility_radius: float = None) -> GridEnvironment:
    """Factory for all 6 environment families required by the benchmark spec."""
    rng = np.random.default_rng(seed)
    H = W = size
    start = (1, 1)
    goal = (H - 2, W - 2)

    if env_type == "static":
        gt = _carve_random_obstacles(H, W, rng, density=0.12)
        gt = (_blur(gt, 1) > 0.35).astype(np.float32)
        n_dyn = 0
    elif env_type == "dynamic":
        gt = _carve_random_obstacles(H, W, rng, density=0.08)
        gt = (_blur(gt, 1) > 0.35).astype(np.float32)
        n_dyn = 6
    elif env_type == "dense":
        gt = _carve_random_obstacles(H, W, rng, density=0.28)
        gt = (_blur(gt, 1) > 0.30).astype(np.float32)
        n_dyn = 4
    elif env_type == "adversarial":
        gt = _carve_random_obstacles(H, W, rng, density=0.12)
        gt = (_blur(gt, 1) > 0.35).astype(np.float32)
        n_dyn = 3
    elif env_type == "sensor_corruption":
        gt = _carve_random_obstacles(H, W, rng, density=0.12)
        gt = (_blur(gt, 1) > 0.35).astype(np.float32)
        n_dyn = 3
    elif env_type == "low_visibility":
        gt = _carve_random_obstacles(H, W, rng, density=0.15)
        gt = (_blur(gt, 1) > 0.35).astype(np.float32)
        n_dyn = 4
    else:
        raise ValueError(env_type)

    gt[start[0], start[1]] = 0.0
    gt[goal[0], goal[1]] = 0.0
    # carve straight clear neighborhoods so a path always exists with reasonable prob.
    gt[start[0]:start[0] + 2, start[1]:start[1] + 2] = 0.0
    gt[goal[0] - 1:goal[0] + 1, goal[1] - 1:goal[1] + 1] = 0.0

    # base sensor noise -> observed occupancy + epistemic uncertainty field
    noise = rng.normal(0, sensor_noise_std, size=(H, W))
    occ_obs = np.clip(gt + noise, 0, 1).astype(np.float32)
    uncertainty = np.abs(rng.normal(sensor_noise_std, sensor_noise_std * 0.5, size=(H, W))).astype(np.float32)

    # adversarial corruption: localized FGSM/PGD-like additive perturbation patches
    if env_type == "adversarial" and corruption_strength > 0:
        n_patches = 5
        for _ in range(n_patches):
            pr, pc = rng.integers(0, H), rng.integers(0, W)
            r0, r1 = max(0, pr - 3), min(H, pr + 3)
            c0, c1 = max(0, pc - 3), min(W, pc + 3)
            occ_obs[r0:r1, c0:c1] = np.clip(
                occ_obs[r0:r1, c0:c1] + rng.choice([-1, 1]) * corruption_strength, 0, 1
            )
            uncertainty[r0:r1, c0:c1] *= 0.3  # adversary makes model *overconfident* (dangerous)

    # sensor corruption: dropout + bias drift across a whole sensor sector
    if env_type == "sensor_corruption" and corruption_strength > 0:
        sector = rng.integers(0, 4)
        if sector == 0:
            occ_obs[: H // 2, :] = np.clip(occ_obs[: H // 2, :] - corruption_strength, 0, 1)
        elif sector == 1:
            occ_obs[H // 2:, :] = np.clip(occ_obs[H // 2:, :] + corruption_strength, 0, 1)
        elif sector == 2:
            occ_obs[:, : W // 2] *= (1 - corruption_strength)
        else:
            occ_obs[:, W // 2:] = np.clip(occ_obs[:, W // 2:] + corruption_strength * rng.random((H, W // 2)), 0, 1)
        uncertainty *= (1 - 0.5 * corruption_strength)  # corrupted sensor under-reports its own uncertainty

    visibility_mask = np.ones((H, W), dtype=np.float32)
    if env_type == "low_visibility":
        vis_r = visibility_radius or (size * 0.28)
        rr, cc = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
        d = np.sqrt((rr - start[0]) ** 2 + (cc - start[1]) ** 2)
        visibility_mask = (d <= vis_r).astype(np.float32)
        # outside visibility radius: occupancy unknown -> default optimistic 0 + high uncertainty
        occ_obs = np.where(visibility_mask > 0, occ_obs, 0.0)
        uncertainty = np.where(visibility_mask > 0, uncertainty, 0.5)

    agents = []
    for _ in range(n_dyn):
        while True:
            pos = rng.uniform(2, size - 3, size=2)
            if np.linalg.norm(pos - np.array(start)) > 4 and np.linalg.norm(pos - np.array(goal)) > 4:
                break
        ang = rng.uniform(0, 2 * np.pi)
        speed = rng.uniform(0.3, 0.8)
        vel = speed * np.array([np.cos(ang), np.sin(ang)])
        agents.append(DynamicAgent(pos=pos, vel=vel))

    return GridEnvironment(
        H=H, W=W, occupancy_gt=gt, occupancy_obs=occ_obs, uncertainty=uncertainty,
        start=start, goal=goal, env_type=env_type, dynamic_agents=agents,
        visibility_mask=visibility_mask, seed=seed,
    )


def generate_map_suite(n_maps: int = 50, size: int = 32, base_seed: int = 1000):
    """Generate the full 50-map benchmark suite, evenly distributed across the 6 env families."""
    maps = []
    per_type = max(1, n_maps // len(ENV_TYPES))
    counter = 0
    for env_type in ENV_TYPES:
        for i in range(per_type):
            seed = base_seed + counter
            maps.append(dict(env_type=env_type, size=size, seed=seed))
            counter += 1
    while len(maps) < n_maps:
        env_type = ENV_TYPES[len(maps) % len(ENV_TYPES)]
        maps.append(dict(env_type=env_type, size=size, seed=base_seed + counter))
        counter += 1
    return maps[:n_maps]
