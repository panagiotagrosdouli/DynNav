from __future__ import annotations

import argparse
from pathlib import Path

from dynnav.experiments.hazard_planner_pilot import (
    run_hazard_planner_pilot,
    write_hazard_planner_pilot_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the development-only proactive safe-return reliability planner pilot."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/hazard_planner_pilot"),
    )
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--hazard-count", type=int, default=6)
    parser.add_argument("--reliability-weight", type=float, default=4.0)
    args = parser.parse_args()
    if args.seeds <= 0:
        raise SystemExit("--seeds must be positive")

    records = run_hazard_planner_pilot(
        tuple(range(args.seeds)),
        hazard_count=args.hazard_count,
        reliability_weight=args.reliability_weight,
    )
    write_hazard_planner_pilot_artifacts(records, args.out_dir)
    print(f"wrote {len(records)} development planner trials to {args.out_dir}")


if __name__ == "__main__":
    main()
