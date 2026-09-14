from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.topology_reliability_benchmark import (
    run_topology_reliability_benchmark,
    write_topology_reliability_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the controlled topology safe-return reliability benchmark."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/topology_reliability"),
    )
    args = parser.parse_args()

    records = run_topology_reliability_benchmark()
    write_topology_reliability_artifacts(records, args.out_dir)
    print(f"wrote {len(records)} trials to {args.out_dir}")


if __name__ == "__main__":
    main()
