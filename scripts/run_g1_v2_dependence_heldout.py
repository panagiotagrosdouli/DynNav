from __future__ import annotations

import argparse

from dynnav.experiments.g1_v2_dependence_heldout import (
    run_g1_v2_heldout_benchmark,
    write_g1_v2_heldout_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the predeclared G1 V2 topology x dependence benchmark."
    )
    parser.add_argument("--trials", type=int, default=2_000)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument(
        "--output-dir",
        default="results/research_gap_program/g1_v2_heldout",
    )
    args = parser.parse_args()

    records = run_g1_v2_heldout_benchmark(
        trials_per_condition=args.trials,
        repetitions=args.repetitions,
        seed=args.seed,
    )
    write_g1_v2_heldout_artifacts(records, args.output_dir)


if __name__ == "__main__":
    main()
