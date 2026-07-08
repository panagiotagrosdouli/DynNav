"""Visualization utilities for DynNav research artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from dynnav.core import GridMap, Trajectory


def plot_risk_heatmap(grid: GridMap, path: Path) -> None:
    """Save a risk heatmap for an occupancy belief grid."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    image = ax.imshow(grid.occupancy, origin="lower")
    fig.colorbar(image, ax=ax, label="P(occupied)")
    ax.set_title("Occupancy-risk heatmap")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_trajectory(grid: GridMap, trajectory: Trajectory, path: Path) -> None:
    """Save a trajectory overlay figure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(grid.occupancy, origin="lower")
    if trajectory.poses:
        xs = [pose.x for pose in trajectory.poses]
        ys = [pose.y for pose in trajectory.poses]
        ax.plot(xs, ys, linewidth=2)
        ax.scatter([xs[0], xs[-1]], [ys[0], ys[-1]], s=50)
    ax.set_title(
        f"Trajectory risk={trajectory.risk:.2f}, "
        f"recoverability={trajectory.recoverability:.2f}"
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_uncertainty(values: np.ndarray, path: Path) -> None:
    """Save a compact uncertainty distribution plot."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(np.asarray(values).ravel(), bins=25)
    ax.set_title("Occupancy uncertainty distribution")
    ax.set_xlabel("P(occupied)")
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
