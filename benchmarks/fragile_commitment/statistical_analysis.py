"""Summarize Fragile Commitment Benchmark CSV results.

The analysis intentionally uses only the Python standard library so that the
first evidence table can be reproduced in minimal environments. It reports
per-planner means, mission-success rates, and normal-approximation 95% confidence
intervals. The raw paired CSV remains the authoritative experimental artifact.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean, stdev
from typing import Iterable

NUMERIC_METRICS = (
    "path_length",
    "route_risk",
    "min_recoverability",
    "mean_recoverability",
    "commitment_loss",
    "bottleneck_exposure",
    "fragility_penalty",
)


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"cannot parse boolean value: {value!r}")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("results CSV contains no rows")
    required = {"seed", "planner", "mission_success", *NUMERIC_METRICS}
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"results CSV is missing columns: {sorted(missing)}")
    return rows


def mean_ci95(values: Iterable[float]) -> tuple[float, float, float]:
    data = list(values)
    if not data:
        raise ValueError("cannot summarize an empty sample")
    mean = fmean(data)
    if len(data) == 1:
        return mean, mean, mean
    margin = 1.96 * stdev(data) / math.sqrt(len(data))
    return mean, mean - margin, mean + margin


def summarize(rows: list[dict[str, str]]) -> list[dict[str, float | int | str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["planner"]].append(row)

    summary: list[dict[str, float | int | str]] = []
    for planner in sorted(grouped):
        planner_rows = grouped[planner]
        successes = [float(_as_bool(row["mission_success"])) for row in planner_rows]
        success_mean, success_low, success_high = mean_ci95(successes)
        record: dict[str, float | int | str] = {
            "planner": planner,
            "trials": len(planner_rows),
            "mission_success_rate": success_mean,
            "mission_success_ci95_low": max(0.0, success_low),
            "mission_success_ci95_high": min(1.0, success_high),
        }
        for metric in NUMERIC_METRICS:
            values = [float(row[metric]) for row in planner_rows]
            mean, low, high = mean_ci95(values)
            record[f"mean_{metric}"] = mean
            record[f"{metric}_ci95_low"] = low
            record[f"{metric}_ci95_high"] = high
        summary.append(record)
    return summary


def write_summary_csv(rows: list[dict[str, float | int | str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, float | int | str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fragile Commitment Benchmark Summary",
        "",
        "| Planner | Trials | Mission success | Path length | Risk | Min recoverability | Commitment loss | Fragility penalty |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {planner} | {trials} | {success:.3f} | {length:.3f} | {risk:.3f} | "
            "{recoverability:.3f} | {loss:.3f} | {penalty:.3f} |".format(
                planner=row["planner"],
                trials=row["trials"],
                success=row["mission_success_rate"],
                length=row["mean_path_length"],
                risk=row["mean_route_risk"],
                recoverability=row["mean_min_recoverability"],
                loss=row["mean_commitment_loss"],
                penalty=row["mean_fragility_penalty"],
            )
        )
    lines.extend(
        [
            "",
            "Confidence intervals are included in the companion summary CSV. They use a normal approximation and are descriptive, not a substitute for paired hypothesis tests on the expanded benchmark families.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--summary-csv", type=Path, default=Path("fragile_commitment_summary.csv"))
    parser.add_argument("--markdown", type=Path, default=Path("fragile_commitment_summary.md"))
    args = parser.parse_args()

    summary = summarize(load_rows(args.results))
    write_summary_csv(summary, args.summary_csv)
    write_markdown(summary, args.markdown)
    print(f"wrote {len(summary)} planner summaries to {args.summary_csv}")
    print(f"wrote paper-ready table to {args.markdown}")


if __name__ == "__main__":
    main()
