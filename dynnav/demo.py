"""Visual demo generation for DynNav's history-conditioned planning mechanism."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from dynnav.commitment_hazard import exact_history_conditioned_return_probability
from dynnav.experiments.history_information_gap_benchmark import _counterfactual_problem


def _pad(path: tuple[tuple[int, int], ...], frames: int) -> tuple[tuple[int, int], ...]:
    return path + (path[-1],) * (frames - len(path))


def generate_demo(
    assets_dir: Path | None = None,
    videos_dir: Path | None = None,
    *,
    closure_probability: float = 0.8,
) -> tuple[Path, Path | None]:
    """Generate the same-place/different-history DynNav visual explanation."""
    assets = Path("assets") if assets_dir is None else assets_dir
    videos = Path("results/videos") if videos_dir is None else videos_dir
    assets.mkdir(parents=True, exist_ok=True)
    videos.mkdir(parents=True, exist_ok=True)

    grid, start, endpoint, risky_path, safe_path, model = _counterfactual_problem(closure_probability)
    risky_return = exact_history_conditioned_return_probability(grid, risky_path, {start}, model)
    safe_return = exact_history_conditioned_return_probability(grid, safe_path, {start}, model)
    frames = max(len(risky_path), len(safe_path))
    risky = _pad(risky_path, frames)
    safe = _pad(safe_path, frames)
    trigger_source, trigger_target = model.closures[0].trigger
    closure_cell = model.closures[0].closure_cell

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharex=True, sharey=True)
    fig.suptitle("DynNav: same place, different execution history", fontsize=14)

    lines = []
    points = []
    for ax, title in zip(axes, ("Triggering history", "Non-triggering history"), strict=True):
        ax.set_title(title)
        ax.set_xlim(-0.5, grid.width - 0.5)
        ax.set_ylim(-0.5, grid.height - 0.5)
        ax.set_aspect("equal")
        ax.set_xticks(range(grid.width))
        ax.set_yticks(range(grid.height))
        ax.grid(True, alpha=0.25)
        for obstacle in grid.obstacles:
            ax.add_patch(Rectangle((obstacle[0] - 0.5, obstacle[1] - 0.5), 1, 1, alpha=0.65))
        ax.scatter([start[0]], [start[1]], marker="s", s=100, label="safe start")
        ax.scatter([endpoint[0]], [endpoint[1]], marker="*", s=150, label="same endpoint x")
        ax.scatter([closure_cell[0]], [closure_cell[1]], marker="X", s=100, label="future closure")
        ax.annotate(
            "trigger",
            xy=trigger_target,
            xytext=(trigger_source[0] - 0.15, trigger_source[1] + 0.55),
            arrowprops={"arrowstyle": "->"},
        )
        (line,) = ax.plot([], [], linewidth=2.5)
        (point,) = ax.plot([], [], marker="o", markersize=8)
        lines.append(line)
        points.append(point)

    axes[0].legend(loc="upper left", fontsize=8)
    status_left = axes[0].text(0.02, 0.02, "", transform=axes[0].transAxes, fontsize=9)
    status_right = axes[1].text(0.02, 0.02, "", transform=axes[1].transAxes, fontsize=9)
    footer = fig.text(0.5, 0.01, "", ha="center", fontsize=11)

    def update(frame: int):
        artists = []
        for path, line, point in zip((risky, safe), lines, points, strict=True):
            shown = path[: frame + 1]
            xs = [cell[0] for cell in shown]
            ys = [cell[1] for cell in shown]
            line.set_data(xs, ys)
            point.set_data([xs[-1]], [ys[-1]])
            artists.extend((line, point))

        risky_triggered = any(
            (a, b) == (trigger_source, trigger_target)
            for a, b in zip(risky[:frame], risky[1 : frame + 1], strict=False)
        )
        safe_triggered = any(
            (a, b) == (trigger_source, trigger_target)
            for a, b in zip(safe[:frame], safe[1 : frame + 1], strict=False)
        )
        status_left.set_text(f"H = {{closure}}\ntrigger activated: {risky_triggered}" if risky_triggered else "H = {}\ntrigger activated: False")
        status_right.set_text(f"H = {{closure}}\ntrigger activated: {safe_triggered}" if safe_triggered else "H = {}\ntrigger activated: False")

        if frame == frames - 1:
            footer.set_text(
                f"Same x = {endpoint}, different H  →  "
                f"P(return | x,H_triggered) = {risky_return:.2f}, "
                f"P(return | x,H_safe) = {safe_return:.2f}"
            )
        else:
            footer.set_text("Execution history determines which future topology hazards are active.")
        return (*artists, status_left, status_right, footer)

    anim = animation.FuncAnimation(fig, update, frames=frames, interval=850, blit=False, repeat_delay=1800)
    fig.tight_layout(rect=(0, 0.07, 1, 0.93))

    gif_path = assets / "history_gap_demo.gif"
    anim.save(gif_path, writer="pillow", fps=1.4)

    mp4_path = videos / "history_gap_demo.mp4"
    try:
        anim.save(mp4_path, fps=1.4)
    except Exception as exc:  # pragma: no cover
        print(f"MP4 export skipped: {exc}")
        mp4_path = None
    finally:
        plt.close(fig)
    return gif_path, mp4_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate DynNav same-state/different-history demo")
    parser.add_argument("--assets-dir", default="assets")
    parser.add_argument("--videos-dir", default="results/videos")
    parser.add_argument("--closure-probability", type=float, default=0.8)
    args = parser.parse_args()
    if not 0.0 <= args.closure_probability <= 1.0:
        parser.error("--closure-probability must be in [0, 1]")
    gif_path, mp4_path = generate_demo(
        Path(args.assets_dir),
        Path(args.videos_dir),
        closure_probability=args.closure_probability,
    )
    print(f"GIF written to {gif_path}")
    if mp4_path is not None:
        print(f"MP4 written to {mp4_path}")


if __name__ == "__main__":
    main()
