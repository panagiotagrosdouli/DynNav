"""Generate an automated DynNav demo GIF and MP4.

The script simulates a deterministic grid scenario, renders trajectory frames,
and exports `assets/demo.gif`. MP4 export is attempted when the local matplotlib
writer stack supports it; failure is reported without failing the GIF path.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt

from dynnav.config import DynNavConfig
from dynnav.planning import RiskAwareAStar
from dynnav.scenarios import generate_scenario


def main() -> None:
    """Generate demo animation artifacts."""
    assets = Path("assets")
    videos = Path("results/videos")
    assets.mkdir(parents=True, exist_ok=True)
    videos.mkdir(parents=True, exist_ok=True)

    config = DynNavConfig(width=40, height=40, n_scenarios=1)
    scenario = generate_scenario(config.width, config.height, config.obstacle_density, config.unknown_fraction, config.seed)
    trajectory, _ = RiskAwareAStar(config.risk_weight, config.returnability_weight, config.cvar_alpha).plan(
        scenario.grid, scenario.start, scenario.goal
    )

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.imshow(scenario.grid.occupancy, origin="lower")
    ax.set_title("DynNav risk-aware rerouting demo")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    (line,) = ax.plot([], [], linewidth=2)
    (point,) = ax.plot([], [], marker="o")
    poses = trajectory.poses or (scenario.start,)

    def update(frame: int):
        xs = [pose.x for pose in poses[: frame + 1]]
        ys = [pose.y for pose in poses[: frame + 1]]
        line.set_data(xs, ys)
        point.set_data([xs[-1]], [ys[-1]])
        return line, point

    anim = animation.FuncAnimation(fig, update, frames=len(poses), interval=80, blit=True)
    anim.save(assets / "demo.gif", writer="pillow", fps=12)
    try:
        anim.save(videos / "demo.mp4", fps=12)
    except Exception as exc:  # pragma: no cover - depends on system codecs
        print(f"MP4 export skipped: {exc}")
    plt.close(fig)


if __name__ == "__main__":
    main()
