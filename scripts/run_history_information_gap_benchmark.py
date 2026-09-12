from __future__ import annotations

import argparse

from dynnav.experiments.history_information_gap_benchmark import (
    run_history_information_gap_benchmark,
    write_history_information_gap_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="results/history_information_gap")
    args = parser.parse_args()
    records = run_history_information_gap_benchmark()
    write_history_information_gap_artifacts(records, args.out_dir)


if __name__ == "__main__":
    main()
