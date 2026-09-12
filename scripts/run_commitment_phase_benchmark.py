from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.commitment_phase_benchmark import (
    run_commitment_phase_benchmark,
    write_commitment_phase_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    records = run_commitment_phase_benchmark()
    write_commitment_phase_artifacts(records, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
