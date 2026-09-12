from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.commitment_trap_benchmark import (
    run_commitment_trap_benchmark,
    write_commitment_trap_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    records = run_commitment_trap_benchmark()
    write_commitment_trap_artifacts(records, args.out_dir)


if __name__ == "__main__":
    main()
