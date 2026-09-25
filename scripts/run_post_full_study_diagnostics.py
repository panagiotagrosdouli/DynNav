from __future__ import annotations

import argparse

from dynnav.experiments.post_full_study_diagnostics import (
    run_post_full_study_diagnostics,
    write_post_full_study_diagnostics,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run post-full-study exploratory G3/G5 diagnostics."
    )
    parser.add_argument("--opportunities", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument(
        "--output",
        default="results/research_gap_program/post_full_study_diagnostics.json",
    )
    args = parser.parse_args()

    result = run_post_full_study_diagnostics(
        opportunities=args.opportunities,
        seed=args.seed,
    )
    write_post_full_study_diagnostics(result, args.output)


if __name__ == "__main__":
    main()
