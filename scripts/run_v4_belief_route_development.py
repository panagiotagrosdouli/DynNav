from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.belief_route_mechanism import (
    run_belief_route_development_benchmark,
    summarize_belief_route_records,
    write_belief_route_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the V4 development-only belief route-choice benchmark."
    )
    parser.add_argument("--trials", type=int, default=1000)
    parser.add_argument("--output-dir", type=Path, default=Path("results/v4_development"))
    args = parser.parse_args()
    if args.trials <= 0:
        raise ValueError("--trials must be positive")

    records = run_belief_route_development_benchmark(
        seeds=tuple(range(args.trials)),
    )
    write_belief_route_artifacts(records, args.output_dir)
    print(json.dumps(summarize_belief_route_records(records), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
