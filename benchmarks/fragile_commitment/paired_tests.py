"""Paired statistical analysis for Fragile Commitment Benchmark results.

The module intentionally uses only the Python standard library. Wilcoxon p-values
use an exact sign-enumeration distribution for small samples and a normal
approximation for larger samples. McNemar uses the exact two-sided binomial test.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class TestResult:
    family: str
    planner_a: str
    planner_b: str
    metric: str
    test: str
    n: int
    statistic: float
    p_value: float
    effect_size: float
    effect_name: str


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position + 1
        while end < len(order) and values[order[end]] == values[order[position]]:
            end += 1
        average_rank = (position + 1 + end) / 2.0
        for index in order[position:end]:
            ranks[index] = average_rank
        position = end
    return ranks


def wilcoxon_signed_rank(x: Iterable[float], y: Iterable[float]) -> tuple[float, float, float, int]:
    """Return W=min(W+, W-), two-sided p-value, rank-biserial effect, n."""
    differences = [float(a) - float(b) for a, b in zip(x, y) if float(a) != float(b)]
    n = len(differences)
    if n == 0:
        return 0.0, 1.0, 0.0, 0

    ranks = _average_ranks([abs(value) for value in differences])
    w_positive = sum(rank for rank, diff in zip(ranks, differences) if diff > 0)
    w_negative = sum(rank for rank, diff in zip(ranks, differences) if diff < 0)
    statistic = min(w_positive, w_negative)
    total_rank = w_positive + w_negative
    effect = (w_positive - w_negative) / total_rank

    if n <= 20:
        observed = statistic
        extreme = 0
        total = 2**n
        for signs in itertools.product((-1, 1), repeat=n):
            positive = sum(rank for rank, sign in zip(ranks, signs) if sign > 0)
            negative = total_rank - positive
            if min(positive, negative) <= observed + 1e-12:
                extreme += 1
        p_value = extreme / total
    else:
        expected = n * (n + 1) / 4.0
        variance = n * (n + 1) * (2 * n + 1) / 24.0
        z = (abs(w_positive - expected) - 0.5) / math.sqrt(variance)
        p_value = math.erfc(max(0.0, z) / math.sqrt(2.0))

    return statistic, min(1.0, p_value), effect, n


def mcnemar_exact(a: Iterable[bool], b: Iterable[bool]) -> tuple[int, float, float, int]:
    """Return discordant minimum, exact p-value, odds-like effect, pair count."""
    pairs = [(bool(left), bool(right)) for left, right in zip(a, b)]
    b_only = sum(left and not right for left, right in pairs)
    c_only = sum(right and not left for left, right in pairs)
    discordant = b_only + c_only
    if discordant == 0:
        return 0, 1.0, 0.0, len(pairs)
    tail = sum(math.comb(discordant, k) for k in range(0, min(b_only, c_only) + 1))
    p_value = min(1.0, 2.0 * tail / (2**discordant))
    effect = (b_only - c_only) / discordant
    return min(b_only, c_only), p_value, effect, len(pairs)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _paired_values(rows: list[dict[str, str]], family: str, planner_a: str, planner_b: str, metric: str) -> tuple[list[str], list[str]]:
    indexed: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for row in rows:
        if row.get("family") == family and row.get("planner") in {planner_a, planner_b}:
            indexed[(row["family"], row["seed"])][row["planner"]] = row[metric]
    left: list[str] = []
    right: list[str] = []
    for pair in indexed.values():
        if planner_a in pair and planner_b in pair:
            left.append(pair[planner_a])
            right.append(pair[planner_b])
    return left, right


def analyse(
    rows: list[dict[str, str]],
    baseline: str = "risk_only",
    candidate: str = "recoverability_aware",
) -> list[TestResult]:
    families = sorted({row["family"] for row in rows})
    continuous = [
        metric
        for metric in ("path_length", "route_risk", "minimum_recoverability", "cumulative_recoverability_loss", "fragility_penalty")
        if rows and metric in rows[0]
    ]
    results: list[TestResult] = []
    for family in families:
        for metric in continuous:
            left, right = _paired_values(rows, family, baseline, candidate, metric)
            statistic, p_value, effect, n = wilcoxon_signed_rank(map(float, left), map(float, right))
            results.append(TestResult(family, baseline, candidate, metric, "wilcoxon_signed_rank", n, statistic, p_value, effect, "rank_biserial"))
        if rows and "mission_success" in rows[0]:
            left, right = _paired_values(rows, family, baseline, candidate, "mission_success")
            to_bool = lambda value: value.strip().lower() in {"1", "true", "yes"}
            statistic, p_value, effect, n = mcnemar_exact(map(to_bool, left), map(to_bool, right))
            results.append(TestResult(family, baseline, candidate, "mission_success", "mcnemar_exact", n, float(statistic), p_value, effect, "discordant_difference"))
    return results


def write_csv(results: list[TestResult], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0])) if results else list(TestResult.__annotations__))
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def write_markdown(results: list[TestResult], output: Path) -> None:
    lines = [
        "| Family | Metric | Test | n | Statistic | p-value | Effect |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.family} | {result.metric} | {result.test} | {result.n} | "
            f"{result.statistic:.4g} | {result.p_value:.4g} | {result.effect_size:.4g} |"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--baseline", default="risk_only")
    parser.add_argument("--candidate", default="recoverability_aware")
    parser.add_argument("--output-csv", type=Path, default=Path("paired_tests.csv"))
    parser.add_argument("--markdown", type=Path, default=Path("paired_tests.md"))
    args = parser.parse_args()
    results = analyse(load_rows(args.results), args.baseline, args.candidate)
    write_csv(results, args.output_csv)
    write_markdown(results, args.markdown)
    significant = sum(result.p_value < 0.05 for result in results)
    print(f"wrote {len(results)} paired tests; {significant} have uncorrected p < 0.05")


if __name__ == "__main__":
    main()
