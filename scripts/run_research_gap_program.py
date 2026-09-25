from __future__ import annotations

import argparse

from dynnav.experiments.research_gap_program import (
    run_research_gap_program,
    write_research_gap_artifact,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the bounded DynNav G1-G5 research programme.")
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument(
        "--output",
        default="results/research_gap_program/g1_g5_summary.json",
    )
    args = parser.parse_args()
    result = run_research_gap_program(trials=args.trials, seed=args.seed)
    write_research_gap_artifact(result, args.output)


if __name__ == "__main__":
    main()
