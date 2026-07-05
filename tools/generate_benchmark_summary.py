#!/usr/bin/env python3
"""Generate a Markdown summary table from DynNav benchmark result files.

The script accepts one or more CSV files that follow the shared benchmark schema
from docs/BENCHMARK_PROTOCOL.md. Extra columns are preserved in the input files
but only the core columns are rendered in the default summary table.

Example:
    python tools/generate_benchmark_summary.py \
        --results results/**/*.csv \
        --output docs/BENCHMARK_RESULTS_SUMMARY.md
"""

from __future__ import annotations

import argparse
import csv
import glob
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable


CORE_COLUMNS = [
    "module_id",
    "experiment_name",
    "method",
    "baseline",
    "n_trials",
    "success_rate",
    "collision_rate",
    "path_length",
    "mean_risk",
    "max_risk",
    "cvar_risk",
    "compute_time_ms",
]

NUMERIC_COLUMNS = {
    "n_trials",
    "success_rate",
    "collision_rate",
    "path_length",
    "mean_risk",
    "max_risk",
    "cvar_risk",
    "compute_time_ms",
}


@dataclass(frozen=True)
class BenchmarkRow:
    values: dict[str, str]
    source_file: str


def expand_patterns(patterns: Iterable[str]) -> list[Path]:
    """Expand shell-style glob patterns into existing CSV paths."""
    paths: list[Path] = []
    for pattern in patterns:
        matches = [Path(p) for p in glob.glob(pattern, recursive=True)]
        paths.extend(path for path in matches if path.is_file())
    return sorted(set(paths))


def read_rows(paths: Iterable[Path]) -> list[BenchmarkRow]:
    """Read benchmark rows from CSV files."""
    rows: list[BenchmarkRow] = []
    for path in paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(BenchmarkRow(values={k: (v or "") for k, v in row.items()}, source_file=str(path)))
    return rows


def _float_or_none(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_by_module(rows: list[BenchmarkRow]) -> list[dict[str, str]]:
    """Aggregate repeated rows by module, experiment, method, and baseline.

    Numeric fields are averaged. Non-numeric fields are kept from the grouping key.
    """
    groups: dict[tuple[str, str, str, str], list[BenchmarkRow]] = {}
    for row in rows:
        key = (
            row.values.get("module_id", ""),
            row.values.get("experiment_name", ""),
            row.values.get("method", ""),
            row.values.get("baseline", ""),
        )
        groups.setdefault(key, []).append(row)

    summaries: list[dict[str, str]] = []
    for (module_id, experiment_name, method, baseline), group_rows in sorted(groups.items()):
        summary: dict[str, str] = {
            "module_id": module_id,
            "experiment_name": experiment_name,
            "method": method,
            "baseline": baseline,
        }
        for column in NUMERIC_COLUMNS:
            values = [
                parsed
                for row in group_rows
                if (parsed := _float_or_none(row.values.get(column, ""))) is not None
            ]
            if values:
                summary[column] = f"{mean(values):.4g}"
            else:
                summary[column] = ""
        summary["source_files"] = ", ".join(sorted({row.source_file for row in group_rows}))
        summaries.append(summary)
    return summaries


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No benchmark rows found.\n"

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, separator, *body]) + "\n"


def build_markdown(rows: list[BenchmarkRow], title: str) -> str:
    summaries = summarize_by_module(rows)
    columns = CORE_COLUMNS + ["source_files"]
    return "\n".join(
        [
            f"# {title}",
            "",
            "This file was generated from CSV benchmark outputs.",
            "",
            "The table reports grouped averages by module, experiment, method, and baseline.",
            "",
            markdown_table(summaries, columns),
            "",
            "## Interpretation notes",
            "",
            "- A generated table is only as credible as the benchmark design that produced the CSV files.",
            "- Single-run rows should be treated as demonstrations, not strong evidence.",
            "- Missing values mean that the source CSV did not provide that metric.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        nargs="+",
        required=True,
        help="One or more CSV paths or glob patterns, e.g. 'results/**/*.csv'.",
    )
    parser.add_argument(
        "--output",
        default="docs/BENCHMARK_RESULTS_SUMMARY.md",
        help="Markdown file to write.",
    )
    parser.add_argument(
        "--title",
        default="DynNav Benchmark Results Summary",
        help="Markdown title.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = expand_patterns(args.results)
    rows = read_rows(paths)
    markdown = build_markdown(rows, args.title)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Read {len(rows)} benchmark rows from {len(paths)} file(s).")
    print(f"Wrote {output_path}.")


if __name__ == "__main__":
    main()
