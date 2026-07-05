#!/usr/bin/env python3
"""Generate publication-style plots for SelfAwareAStar randomized results.

Run from repository root after generating the randomized benchmark CSV:

    python benchmarks/self_aware_astar/randomized_ablation_benchmark.py --seeds 50
    python benchmarks/self_aware_astar/plot_randomized_results.py

The script requires matplotlib. It intentionally does not require pandas or
seaborn so the plotting layer stays lightweight.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

DEFAULT_INPUT = Path("results/self_aware_astar_randomized_ablation.csv")
DEFAULT_OUTPUT_DIR = Path("results/figures/self_aware_astar")
DEFAULT_REPORT = Path("results/self_aware_astar_figure_index.md")

PLOT_METRICS = [
    ("mean_risk", "Mean risk", "Lower is better"),
    ("max_risk", "Max risk", "Lower is better"),
    ("recoverability", "Recoverability", "Higher is better"),
    ("information_gain", "Information gain", "Higher is better"),
    ("path_length", "Path length", "Lower is usually better"),
    ("compute_time_ms", "Compute time (ms)", "Lower is better"),
]


def require_matplotlib():
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required for plotting. Install it with `pip install matplotlib`."
        ) from exc
    return plt


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def grouped_values(rows: list[dict[str, str]], metric: str) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        try:
            groups[row["method"]].append(float(row[metric]))
        except (KeyError, ValueError):
            continue
    return dict(groups)


def summarize(groups: dict[str, list[float]]) -> tuple[list[str], list[float], list[float]]:
    methods = sorted(groups)
    means = [mean(groups[method]) for method in methods]
    errors = [pstdev(groups[method]) if len(groups[method]) > 1 else 0.0 for method in methods]
    return methods, means, errors


def safe_filename(metric: str) -> str:
    return f"{metric}_comparison.png"


def plot_metric(rows: list[dict[str, str]], metric: str, title: str, subtitle: str, output_dir: Path) -> Path:
    plt = require_matplotlib()
    groups = grouped_values(rows, metric)
    methods, means, errors = summarize(groups)

    if not methods:
        raise ValueError(f"no values found for metric {metric!r}")

    fig, ax = plt.subplots(figsize=(10, 5))
    positions = list(range(len(methods)))
    ax.bar(positions, means, yerr=errors, capsize=5)
    ax.set_xticks(positions)
    ax.set_xticklabels(methods, rotation=30, ha="right")
    ax.set_ylabel(metric)
    ax.set_title(f"{title}\n{subtitle}")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / safe_filename(metric)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def build_index(generated: list[tuple[str, Path]], output_dir: Path) -> str:
    lines = [
        "# SelfAwareAStar Figure Index",
        "",
        "Generated figures for the randomized SelfAwareAStar benchmark.",
        "",
        "These figures visualize mean values with standard-deviation error bars across randomized synthetic maps.",
        "",
        "| Metric | Figure |",
        "|---|---|",
    ]
    for metric, path in generated:
        rel = path.as_posix()
        lines.append(f"| `{metric}` | `{rel}` |")
    lines.extend(
        [
            "",
            "## Interpretation note",
            "",
            "The plots are visual summaries of synthetic benchmark data. They should be read together with the statistical report, which includes confidence intervals and effect sizes.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Randomized benchmark CSV path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for PNG figures.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Markdown figure index path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_rows(args.input)
    generated: list[tuple[str, Path]] = []
    for metric, title, subtitle in PLOT_METRICS:
        path = plot_metric(rows, metric, title, subtitle, args.output_dir)
        generated.append((metric, path))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(build_index(generated, args.output_dir), encoding="utf-8")
    print(f"Generated {len(generated)} figure(s) in {args.output_dir}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
