from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.v4_correlation_benchmark import (
    run_correlation_reliability_benchmark,
    summarize_correlation_reliability,
    write_correlation_reliability_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the V4 equal-marginal correlation development study."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/v4_correlation"),
    )
    args = parser.parse_args()

    records = run_correlation_reliability_benchmark()
    write_correlation_reliability_artifacts(records, args.output_dir)
    print(
        json.dumps(
            summarize_correlation_reliability(records),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
