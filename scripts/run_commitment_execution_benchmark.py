from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.commitment_execution_benchmark import (
    run_commitment_execution_benchmark,
    write_commitment_execution_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    records = run_commitment_execution_benchmark()
    write_commitment_execution_artifacts(records, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
