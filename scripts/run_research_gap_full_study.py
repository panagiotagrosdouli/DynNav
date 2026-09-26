from __future__ import annotations

import argparse

from dynnav.experiments.research_gap_full_study import (
    run_full_research_gap_study,
    write_full_study,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen synthetic DynNav G1-G5 full study."
    )
    parser.add_argument("--trials-per-condition", type=int, default=2000)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument(
        "--output",
        default="results/research_gap_program/full_study.json",
    )
    args = parser.parse_args()
    result = run_full_research_gap_study(
        trials_per_condition=args.trials_per_condition,
        repetitions=args.repetitions,
        seed=args.seed,
    )
    write_full_study(result, args.output)


if __name__ == "__main__":
    main()
