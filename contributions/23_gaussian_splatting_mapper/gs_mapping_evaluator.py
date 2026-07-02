"""Gaussian-splatting map evaluation utilities for Contribution 23.

The mapper should be evaluated as a navigation map, not only as a 3D structure.
This module scores projected occupancy and exploration usefulness:

- occupancy IoU against a synthetic ground-truth grid,
- precision / recall for occupied cells,
- uncertainty alignment with unobserved regions,
- frontier precision proxy,
- Gaussian efficiency.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from gaussian_splatting_map import GSMapConfig, GaussianSplattingMap


@dataclass(frozen=True)
class GSMappingMetrics:
    scenario: str
    n_frames: int
    n_gaussians: int
    occupancy_iou: float
    occupancy_precision: float
    occupancy_recall: float
    uncertainty_unknown_gap: float
    frontier_count: int
    frontier_precision_proxy: float
    gaussians_per_observed_cell: float

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def synthetic_room_points(seed: int, n_points: int = 120, clutter: bool = False) -> np.ndarray:
    rng = np.random.default_rng(seed)
    walls = []
    xs = rng.uniform(-3.0, 3.0, n_points // 4)
    ys = rng.uniform(-3.0, 3.0, n_points // 4)
    walls.append(np.column_stack([xs, np.full_like(xs, -3.0), rng.uniform(0.2, 1.5, len(xs))]))
    walls.append(np.column_stack([xs, np.full_like(xs, 3.0), rng.uniform(0.2, 1.5, len(xs))]))
    walls.append(np.column_stack([np.full_like(ys, -3.0), ys, rng.uniform(0.2, 1.5, len(ys))]))
    walls.append(np.column_stack([np.full_like(ys, 3.0), ys, rng.uniform(0.2, 1.5, len(ys))]))
    points = np.vstack(walls)
    if clutter:
        blob = rng.normal(loc=(0.8, 0.4, 0.7), scale=(0.35, 0.35, 0.25), size=(n_points // 3, 3))
        points = np.vstack([points, blob])
    points += rng.normal(0.0, 0.03, points.shape)
    return points


def ground_truth_grid(config: GSMapConfig, clutter: bool = False) -> np.ndarray:
    H, W = config.grid_size
    res = config.grid_resolution
    grid = np.zeros((H, W), dtype=float)

    def mark_xy(x: float, y: float, radius: int = 1) -> None:
        cx = int(x / res) + W // 2
        cy = int(y / res) + H // 2
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < W and 0 <= ny < H:
                    grid[ny, nx] = 1.0

    coords = np.arange(-3.0, 3.01, res)
    for x in coords:
        mark_xy(float(x), -3.0)
        mark_xy(float(x), 3.0)
    for y in coords:
        mark_xy(-3.0, float(y))
        mark_xy(3.0, float(y))
    if clutter:
        for x in np.linspace(0.3, 1.3, 8):
            for y in np.linspace(-0.1, 0.9, 8):
                mark_xy(float(x), float(y), radius=1)
    return grid


def occupancy_scores(pred: np.ndarray, truth: np.ndarray, threshold: float = 0.3) -> tuple[float, float, float]:
    p = pred >= threshold
    y = truth >= 0.5
    tp = float(np.logical_and(p, y).sum())
    fp = float(np.logical_and(p, ~y).sum())
    fn = float(np.logical_and(~p, y).sum())
    iou = tp / max(1.0, tp + fp + fn)
    precision = tp / max(1.0, tp + fp)
    recall = tp / max(1.0, tp + fn)
    return float(iou), float(precision), float(recall)


def evaluate_gaussian_map(scenario: str, n_frames: int = 10, clutter: bool = False) -> GSMappingMetrics:
    cfg = GSMapConfig(grid_resolution=0.1, grid_size=(90, 90), merge_threshold=2.8)
    gsmap = GaussianSplattingMap(cfg)
    for frame_idx in range(n_frames):
        pts = synthetic_room_points(1000 + frame_idx, clutter=clutter)
        pose = np.eye(4)
        pose[:2, 3] = np.array([0.03 * frame_idx, -0.02 * frame_idx])
        gsmap.add_frame(pts, pose=pose)

    occ = gsmap.to_occupancy_grid()
    truth = ground_truth_grid(cfg, clutter=clutter)
    unc = gsmap.uncertainty_map()
    iou, precision, recall = occupancy_scores(occ, truth)
    unknown = truth < 0.5
    known_occ = truth >= 0.5
    uncertainty_gap = float(np.mean(unc[unknown]) - np.mean(unc[known_occ]))
    frontiers = gsmap.frontier_cells()
    frontier_precision = float(sum(truth[r, c] < 0.5 for r, c in frontiers) / max(1, len(frontiers)))
    observed_cells = max(1, int((occ > 0.05).sum()))

    return GSMappingMetrics(
        scenario=scenario,
        n_frames=n_frames,
        n_gaussians=len(gsmap.gaussians),
        occupancy_iou=iou,
        occupancy_precision=precision,
        occupancy_recall=recall,
        uncertainty_unknown_gap=uncertainty_gap,
        frontier_count=len(frontiers),
        frontier_precision_proxy=frontier_precision,
        gaussians_per_observed_cell=float(len(gsmap.gaussians) / observed_cells),
    )
