from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.forced_hazard_choice_benchmark import (
    run_forced_hazard_choice_benchmark,
    write_forced_hazard_choice_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    records = run_forced_hazard_choice_benchmark()
    write_forced_hazard_choice_artifacts(records, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
