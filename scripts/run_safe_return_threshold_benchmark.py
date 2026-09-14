#!/usr/bin/env python3
"""Run the hard safe-return threshold sensitivity benchmark."""
from __future__ import annotations

import argparse

from dynnav.experiments.safe_return_threshold_benchmark import (
    run_safe_return_threshold_benchmark,
    write_safe_return_threshold_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-count", type=int, default=3)
    parser.add_argument("--out-dir", default="results/safe_return_threshold")
    args = parser.parse_args()

    records = run_safe_return_threshold_benchmark(module_count=args.module_count)
    write_safe_return_threshold_artifacts(records, args.out_dir)


if __name__ == "__main__":
    main()
