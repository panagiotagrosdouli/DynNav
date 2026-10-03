from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.v4_belief_scaling import (
    run_belief_scaling_benchmark,
    summarize_belief_scaling,
    write_belief_scaling_artifacts,
)


def _counts(value: str) -> tuple[int, ...]:
    counts = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not counts:
        raise argparse.ArgumentTypeError("count list cannot be empty")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V4 belief scaling measurements.")
    parser.add_argument("--hazard-counts", type=_counts, default=(1, 2, 4, 6, 8, 10, 12))
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--per-call-budget-s", type=float, default=10.0)
    parser.add_argument("--output-dir", type=Path, default=Path("results/v4_belief_scaling"))
    args = parser.parse_args()

    records = run_belief_scaling_benchmark(
        hazard_counts=args.hazard_counts,
        warmups=args.warmups,
        repetitions=args.repetitions,
        per_call_budget_s=args.per_call_budget_s,
    )
    write_belief_scaling_artifacts(records, args.output_dir)
    print(json.dumps(summarize_belief_scaling(records), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
