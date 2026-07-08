"""Generate an automated DynNav demo GIF and MP4.

The script simulates a deterministic grid scenario, renders trajectory frames,
and exports `assets/demo.gif` and `results/videos/demo.mp4` when the local writer
stack supports MP4. It requires no manual editing.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt

from dynnav.config import DynNavConfig
from dynnav.planning import RiskAwareAStar
from dynnav.research_modules import MissionRiskEstimator, UncertaintyState
from dynnav.scenarios import generate_scenario

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Generate demo animation artifacts."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    assets = Path("assets")
    videos = Path("results/videos")
    assets.mkdir(parents=True, exist_ok=True)
    videos.mkdir(parents=True, exist_ok=True)

    config = DynNavConfig(width=40, height=40, n_scenarios=1)
    scenario = generate_scenario(
        config.width,
        config.height,
        config.obstacle_density,
        config.unknown_fraction,
        config.seed,
    )
    trajectory, _ = RiskAwareAStar(
        config.risk_weight,
        config.returnability_weight,
        config.cvar_alpha,
    ).plan(scenario.grid, scenario.start, scenario.goal)
    report = MissionRiskEstimator().evaluate(
        trajectory,
        UncertaintyState(
            map_entropy=config.unknown_fraction,
            localization_std=0.15,
            obstacle_velocity_std=0.10,
            perception_dropout=0.05,
        ),
    )

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.imshow(scenario.grid.occupancy, origin="lower")
    ax.set_title("DynNav risk-aware rerouting demo")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.text(
        0.02,
        0.98,
        f"mode={report.recommended_mode.value}\nrisk={report.expected_collision_risk:.2f}\nrecoverability={report.recoverability:.2f}",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round", "alpha": 0.8},
    )
    ax.scatter([scenario.start.x], [scenario.start.y], marker="s", label="start")
    ax.scatter([scenario.goal.x], [scenario.goal.y], marker="*", label="goal")
    (line,) = ax.plot([], [], linewidth=2, label="trajectory")
    (point,) = ax.plot([], [], marker="o")
    ax.legend(loc="lower right")
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
    mp4_path = videos / "demo.mp4"
    anim.save(gif_path, writer="pillow", fps=12)
    LOGGER.info("wrote %s", gif_path)
    try:
        anim.save(mp4_path, fps=12)
        LOGGER.info("wrote %s", mp4_path)
    except Exception as exc:  # pragma: no cover - depends on system codecs
        LOGGER.warning("MP4 export skipped: %s", exc)
    plt.close(fig)


if __name__ == "__main__":
    main()
