from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.geometric_heldout_benchmark import (
    run_geometric_heldout_benchmark,
    summarize_geometric_heldout,
    write_geometric_heldout_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen geometric held-out benchmark."
    )
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--recoverability-weight", type=float, default=8.0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/geometric_heldout"),
    )
    args = parser.parse_args()
    if args.seeds <= 0:
        raise SystemExit("--seeds must be positive")

    records = run_geometric_heldout_benchmark(
        seeds=tuple(range(args.seeds)),
        recoverability_weight=args.recoverability_weight,
    )
    write_geometric_heldout_artifacts(records, args.output_dir)
    print(json.dumps(summarize_geometric_heldout(records), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
