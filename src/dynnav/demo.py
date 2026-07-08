"""Command-line demo generation for DynNav.

This module backs the ``dynnav-demo`` console script declared in ``pyproject.toml``.
It intentionally mirrors the lightweight, non-ROS demo workflow so the installed
package exposes a working entry point.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt

from dynnav.config import DynNavConfig
from dynnav.planning import RiskAwareAStar
from dynnav.scenarios import generate_scenario


def generate_demo(
    assets_dir: Path | None = None,
    videos_dir: Path | None = None,
    *,
    width: int = 40,
    height: int = 40,
    seed: int = 0,
) -> tuple[Path, Path | None]:
    """Generate a deterministic DynNav GIF and optionally an MP4.

    Args:
        assets_dir: Directory where ``demo.gif`` is written.
        videos_dir: Directory where ``demo.mp4`` is attempted.
        width: Scenario grid width.
        height: Scenario grid height.
        seed: Deterministic scenario seed.

    Returns:
        A pair containing the GIF path and the MP4 path when export succeeds.
    """
    assets = Path("assets") if assets_dir is None else assets_dir
    videos = Path("results/videos") if videos_dir is None else videos_dir
    assets.mkdir(parents=True, exist_ok=True)
    videos.mkdir(parents=True, exist_ok=True)

    config = DynNavConfig(width=width, height=height, n_scenarios=1, seed=seed)
    scenario = generate_scenario(
        config.width,
        config.height,
        config.obstacle_density,
        config.unknown_fraction,
        config.seed,
    )
    trajectory, _ = RiskAwareAStar(
        risk_weight=config.risk_weight,
        returnability_weight=config.returnability_weight,
        alpha=config.cvar_alpha,
        max_expansions=config.max_expansions,
    ).plan(scenario.grid, scenario.start, scenario.goal)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(scenario.grid.occupancy, origin="lower")
    ax.set_title("DynNav risk-aware rerouting demo")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    (line,) = ax.plot([], [], linewidth=2)
    (point,) = ax.plot([], [], marker="o")
    poses = trajectory.poses or (scenario.start,)

    def update(frame: int) -> tuple[plt.Line2D, plt.Line2D]:
        xs = [pose.x for pose in poses[: frame + 1]]
        ys = [pose.y for pose in poses[: frame + 1]]
        line.set_data(xs, ys)
        point.set_data([xs[-1]], [ys[-1]])
        return line, point

    anim = animation.FuncAnimation(
        fig,
        update,
        frames=len(poses),
        interval=80,
        blit=True,
    )

    gif_path = assets / "demo.gif"
    anim.save(gif_path, writer="pillow", fps=12)

    mp4_path = videos / "demo.mp4"
    try:
        anim.save(mp4_path, fps=12)
    except Exception as exc:  # pragma: no cover - depends on system codecs
        print(f"MP4 export skipped: {exc}")
        mp4_path = None
    finally:
        plt.close(fig)

    return gif_path, mp4_path


def main() -> None:
    """Run the installed DynNav demo generator."""
    parser = argparse.ArgumentParser(description="Generate DynNav demo artifacts")
    parser.add_argument("--assets-dir", default="assets")
    parser.add_argument("--videos-dir", default="results/videos")
    parser.add_argument("--width", type=int, default=40)
    parser.add_argument("--height", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    gif_path, mp4_path = generate_demo(
        Path(args.assets_dir),
        Path(args.videos_dir),
        width=args.width,
        height=args.height,
        seed=args.seed,
    )
    print(f"GIF written to {gif_path}")
    if mp4_path is not None:
        print(f"MP4 written to {mp4_path}")


if __name__ == "__main__":
    main()
