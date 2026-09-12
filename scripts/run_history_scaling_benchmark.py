from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.history_scaling_benchmark import (
    run_history_scaling_benchmark,
    write_history_scaling_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    records = run_history_scaling_benchmark()
    write_history_scaling_artifacts(records, args.out_dir)


if __name__ == "__main__":
    main()
