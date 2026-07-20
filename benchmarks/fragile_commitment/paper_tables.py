"""Generate publication-ready tables for the Fragile Commitment Benchmark."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

PLANNER_ORDER = ("shortest", "risk_only", "safe_return", "recoverability_aware")
METRICS = (
    "mission_success",
    "path_length",
    "route_risk",
    "minimum_recoverability",
    "cumulative_recoverability_loss",
    "fragility_penalty",
)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _number(value: str) -> float:
    lowered = value.strip().lower()
    if lowered in {"true", "yes"}:
        return 1.0
    if lowered in {"false", "no"}:
        return 0.0
    return float(value)


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("family", "overall"), row["planner"])].append(row)

    output: list[dict[str, str]] = []
    families = sorted({family for family, _ in grouped})
    for family in ["overall", *families]:
        for planner in PLANNER_ORDER:
            selected = (
                [row for row in rows if row["planner"] == planner]
                if family == "overall"
                else grouped.get((family, planner), [])
            )
            if not selected:
                continue
            record = {"family": family, "planner": planner, "n": str(len(selected))}
            for metric in METRICS:
                if metric in selected[0]:
                    record[metric] = f"{mean(_number(row[metric]) for row in selected):.4f}"
            output.append(record)
    return output


def _escape_latex(text: str) -> str:
    return text.replace("_", r"\_").replace("%", r"\%")


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["family", "planner", "n", *METRICS]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]], path: Path) -> None:
    fields = list(rows[0]) if rows else ["family", "planner", "n", *METRICS]
    lines = [
        "| " + " | ".join(fields) + " |",
        "|" + "|".join("---" for _ in fields) + "|",
    ]
    lines.extend("| " + " | ".join(row.get(field, "") for field in fields) + " |" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(rows: list[dict[str, str]], path: Path, caption: str, label: str) -> None:
    fields = list(rows[0]) if rows else ["family", "planner", "n", *METRICS]
    alignment = "ll" + "r" * (len(fields) - 2)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{_escape_latex(caption)}}}",
        rf"\label{{{_escape_latex(label)}}}",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\toprule",
        " & ".join(_escape_latex(field) for field in fields) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(_escape_latex(row.get(field, "")) for field in fields) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_statistical_tables(rows: list[dict[str, str]], output_dir: Path) -> None:
    if not rows:
        return
    fields = [field for field in ("family", "metric", "test", "n", "statistic", "p_value", "effect_size", "effect_name") if field in rows[0]]
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    write_csv(normalized, output_dir / "statistical_tests.csv")
    write_markdown(normalized, output_dir / "statistical_tests.md")
    write_latex(normalized, output_dir / "statistical_tests.tex", "Paired hypothesis tests", "tab:paired-tests")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("paired_tests", type=Path, nargs="?")
    parser.add_argument("--output-dir", type=Path, default=Path("paper/tables/fragile_commitment"))
    args = parser.parse_args()

    summary = aggregate(load_csv(args.results))
    write_csv(summary, args.output_dir / "planner_summary.csv")
    write_markdown(summary, args.output_dir / "planner_summary.md")
    write_latex(summary, args.output_dir / "planner_summary.tex", "Fragile Commitment Benchmark summary", "tab:fragile-commitment-summary")

    if args.paired_tests:
        write_statistical_tables(load_csv(args.paired_tests), args.output_dir)
    print(f"wrote paper tables to {args.output_dir}")


if __name__ == "__main__":
    main()
