#!/usr/bin/env python3
"""Run frozen held-out heterogeneous history generalization benchmark."""
from __future__ import annotations

import argparse

from dynnav.experiments.heldout_history_generalization import (
    run_heldout_history_generalization,
    write_heldout_history_generalization_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="results/heldout_history_generalization")
    parser.add_argument("--seeds", type=int, default=500)
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")

    records = run_heldout_history_generalization(seeds=tuple(range(args.seeds)))
    write_heldout_history_generalization_artifacts(records, args.out_dir)


if __name__ == "__main__":
    main()
