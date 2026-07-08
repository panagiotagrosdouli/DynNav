"""Generate static research figures for documentation and results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from dynnav.config import DynNavConfig
from dynnav.planning import RiskAwareAStar
from dynnav.scenarios import generate_scenario
from dynnav.visualization import plot_risk_heatmap, plot_trajectory, plot_uncertainty


def write_diagram(path: Path, title: str, nodes: list[str]) -> None:
    """Write a simple publication-friendly pipeline diagram."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 2.2))
    ax.axis("off")
    ax.set_title(title)
    for idx, node in enumerate(nodes):
        ax.text(
            idx,
            0.5,
            node,
            ha="center",
            va="center",
            bbox={"boxstyle": "round", "fc": "white"},
        )
        if idx < len(nodes) - 1:
            ax.annotate(
                "",
                xy=(idx + 0.42, 0.5),
                xytext=(idx + 0.58, 0.5),
                arrowprops={"arrowstyle": "->"},
            )
    ax.set_xlim(-0.6, len(nodes) - 0.4)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    """Generate diagrams and baseline figures."""
    config = DynNavConfig()
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

    write_diagram(
        Path("assets/architecture.png"),
        "DynNav architecture",
        ["Perception", "Belief", "Risk Planner", "Monitor", "Control"],
    )
    write_diagram(
        Path("assets/navigation_pipeline.png"),
        "Navigation pipeline",
        ["Sense", "Propagate", "Plan", "Monitor", "Reroute"],
    )
    plot_risk_heatmap(scenario.grid, Path("assets/risk_heatmap.png"))
    plot_trajectory(scenario.grid, trajectory, Path("assets/trajectory.png"))
    plot_uncertainty(scenario.grid.occupancy, Path("assets/uncertainty.png"))
    plot_risk_heatmap(scenario.grid, Path("results/figures/risk_heatmap.png"))
    plot_trajectory(scenario.grid, trajectory, Path("results/figures/trajectory.png"))


if __name__ == "__main__":
    main()
