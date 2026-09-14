from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.geometric_pareto_benchmark import (
    run_geometric_pareto_benchmark,
    summarize_geometric_pareto,
    write_geometric_pareto_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen geometric Pareto sweep.")
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/geometric_pareto"),
    )
    args = parser.parse_args()
    if args.seeds <= 0:
        raise SystemExit("--seeds must be positive")

    records = run_geometric_pareto_benchmark(seeds=tuple(range(args.seeds)))
    write_geometric_pareto_artifacts(records, args.output_dir)
    print(json.dumps(summarize_geometric_pareto(records), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
