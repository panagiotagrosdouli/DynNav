#!/usr/bin/env python3
"""Statistical analysis for the randomized Dynamic SelfAwareAStar benchmark.

Run after generating the randomized benchmark CSV:

    python benchmarks/dynamic_self_aware_astar/randomized_dynamic_benchmark.py --seeds 50
    python benchmarks/dynamic_self_aware_astar/statistical_analysis.py
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable

DEFAULT_INPUT = Path("results/dynamic_self_aware_astar_randomized.csv")
DEFAULT_REPORT = Path("results/dynamic_self_aware_astar_statistical_report.md")

KEY_METRICS = [
    "success_rate",
    "collision_rate",
    "path_length",
    "replans",
    "nodes_expanded",
    "mean_risk",
    "max_risk",
    "recoverability",
    "compute_time_ms",
]


@dataclass(frozen=True)
class SummaryStats:
    mean: float
    std: float
    ci_low: float
    ci_high: float
    n: int


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def grouped_values(rows: Iterable[dict[str, str]], metric: str) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        try:
            grouped[row["method"]].append(float(row[metric]))
        except (KeyError, ValueError):
            continue
    return dict(grouped)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * q)))
    return ordered[index]


def bootstrap_ci(values: list[float], n_bootstrap: int, confidence: float, seed: int) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(n_bootstrap):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(mean(sample))
    alpha = (1.0 - confidence) / 2.0
    return percentile(means, alpha), percentile(means, 1.0 - alpha)


def summarize(values: list[float], n_bootstrap: int, confidence: float, seed: int) -> SummaryStats:
    if not values:
        return SummaryStats(0.0, 0.0, 0.0, 0.0, 0)
    ci_low, ci_high = bootstrap_ci(values, n_bootstrap, confidence, seed)
    return SummaryStats(
        mean=mean(values),
        std=pstdev(values) if len(values) > 1 else 0.0,
        ci_low=ci_low,
        ci_high=ci_high,
        n=len(values),
    )


def cohens_d(reference: list[float], candidate: list[float]) -> float:
    if len(reference) < 2 or len(candidate) < 2:
        return 0.0
    ref_std = pstdev(reference)
    cand_std = pstdev(candidate)
    pooled = math.sqrt((ref_std**2 + cand_std**2) / 2.0)
    if pooled == 0.0:
        return 0.0
    return (mean(candidate) - mean(reference)) / pooled


def preferred_direction(metric: str) -> str:
    if metric in {"success_rate", "recoverability"}:
        return "higher"
    return "lower"


def build_report(
    rows: list[dict[str, str]],
    baseline: str,
    n_bootstrap: int,
    confidence: float,
    seed: int,
) -> str:
    methods = sorted({row["method"] for row in rows})
    lines = [
        "# Dynamic SelfAwareAStar Statistical Evaluation",
        "",
        f"Rows analysed: {len(rows)}",
        f"Bootstrap samples: {n_bootstrap}",
        f"Confidence level: {confidence:.0%}",
        f"Baseline: `{baseline}`",
        "",
    ]

    for metric in KEY_METRICS:
        groups = grouped_values(rows, metric)
        if not groups:
            continue
        baseline_values = groups.get(baseline, [])
        lines.extend(
            [
                f"## `{metric}`",
                "",
                f"Preferred direction: **{preferred_direction(metric)}**.",
                "",
                "| Method | n | Mean | Std | CI low | CI high | Cohen's d vs baseline |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for method in methods:
            values = groups.get(method, [])
            stats = summarize(values, n_bootstrap, confidence, seed + abs(hash(metric + method)) % 10_000)
            effect = cohens_d(baseline_values, values) if method != baseline else 0.0
            lines.append(
                f"| {method} | {stats.n} | {stats.mean:.4f} | {stats.std:.4f} | "
                f"{stats.ci_low:.4f} | {stats.ci_high:.4f} | {effect:.4f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation guide",
            "",
            "- Confidence intervals are bootstrap intervals over randomized dynamic scenarios.",
            "- Cohen's d is method mean minus baseline mean divided by pooled standard deviation.",
            "- Positive effect size helps only for metrics where higher is better; for risk, collisions, path length, replans, and compute time, negative values are usually preferable.",
            "- This is synthetic benchmark evidence, not real-robot validation.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--baseline", default="static_self_aware_astar")
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=123)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_rows(args.input)
    report = build_report(rows, args.baseline, args.bootstrap, args.confidence, args.seed)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
