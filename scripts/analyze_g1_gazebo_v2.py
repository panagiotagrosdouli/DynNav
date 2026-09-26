from __future__ import annotations

import argparse
import json

from dynnav.evaluation.g1_gazebo_v2_analysis import analyze_g1_gazebo_v2_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze canonical G1 Gazebo V2 results.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260925)
    args = parser.parse_args()
    summary = analyze_g1_gazebo_v2_file(
        args.input,
        args.output,
        bootstrap_resamples=args.bootstrap_resamples,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
