"""Generate publication-oriented figures from Fragile Commitment results."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import fmean

PLANNER_ORDER = ("shortest", "risk_only", "safe_return", "recoverability_aware")
METRICS = (
    "mission_success",
    "minimum_recoverability",
    "cumulative_recoverability_loss",
    "fragility_penalty",
    "route_risk",
    "path_length",
)


def _as_float(value: str) -> float:
    lowered = value.strip().lower()
    if lowered in {"true", "yes"}:
        return 1.0
    if lowered in {"false", "no"}:
        return 0.0
    return float(value)


def load_results(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("results CSV is empty")
    required = {"family", "seed", "planner", *METRICS}
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"results CSV is missing columns: {sorted(missing)}")
    return rows


def aggregate(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, float]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["family"], row["planner"])].append(row)

    summary: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for (family, planner), observations in grouped.items():
        summary[family][planner] = {
            metric: fmean(_as_float(row[metric]) for row in observations)
            for metric in METRICS
        }
    return dict(summary)


def _planner_sequence(planners: set[str]) -> list[str]:
    ordered = [planner for planner in PLANNER_ORDER if planner in planners]
    return ordered + sorted(planners.difference(ordered))


def plot_metric_by_family(
    summary: dict[str, dict[str, dict[str, float]]],
    metric: str,
    output: Path,
) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    families = sorted(summary)
    planners = _planner_sequence(
        {planner for family in summary.values() for planner in family}
    )
    x = np.arange(len(families), dtype=float)
    width = 0.8 / max(1, len(planners))

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for index, planner in enumerate(planners):
        values = [summary[family].get(planner, {}).get(metric, float("nan")) for family in families]
        offset = (index - (len(planners) - 1) / 2) * width
        ax.bar(x + offset, values, width=width, label=planner.replace("_", " "))

    ax.set_xticks(x, families)
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_xlabel("Topology family")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def plot_risk_recoverability(rows: list[dict[str, str]], output: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    planners = _planner_sequence({row["planner"] for row in rows})
    for planner in planners:
        selected = [row for row in rows if row["planner"] == planner]
        ax.scatter(
            [_as_float(row["route_risk"]) for row in selected],
            [_as_float(row["minimum_recoverability"]) for row in selected],
            s=18,
            alpha=0.55,
            label=planner.replace("_", " "),
        )
    ax.set_xlabel("Route risk")
    ax.set_ylabel("Minimum recoverability")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def generate_figures(rows: list[dict[str, str]], output_dir: Path, extension: str) -> list[Path]:
    summary = aggregate(rows)
    outputs: list[Path] = []
    for metric in (
        "mission_success",
        "minimum_recoverability",
        "cumulative_recoverability_loss",
        "fragility_penalty",
    ):
        target = output_dir / f"{metric}_by_family.{extension}"
        plot_metric_by_family(summary, metric, target)
        outputs.append(target)
    scatter = output_dir / f"risk_vs_recoverability.{extension}"
    plot_risk_recoverability(rows, scatter)
    outputs.append(scatter)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_csv", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("paper/figures/fragile_commitment"))
    parser.add_argument("--format", choices=("pdf", "svg", "png"), default="pdf")
    args = parser.parse_args()

    outputs = generate_figures(load_results(args.results_csv), args.output_dir, args.format)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
