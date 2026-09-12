from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.recoverability_estimator_pilot import (
    run_estimator_pilot,
    write_estimator_pilot_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the development-only exact recoverability estimator pilot."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/recoverability_estimator_pilot"),
    )
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--hazard-count", type=int, default=6)
    args = parser.parse_args()
    if args.seeds <= 0:
        raise SystemExit("--seeds must be positive")

    records = run_estimator_pilot(
        tuple(range(args.seeds)),
        hazard_count=args.hazard_count,
    )
    write_estimator_pilot_artifacts(records, args.out_dir)
    print(f"wrote {len(records)} development trials to {args.out_dir}")


if __name__ == "__main__":
    main()
