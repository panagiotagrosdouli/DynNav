from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.noisy_activation_benchmark import (
    run_noisy_activation_benchmark,
    summarize_noisy_activation,
    write_noisy_activation_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the noisy action-trigger activation benchmark.")
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("results/noisy_activation"))
    args = parser.parse_args()
    records = run_noisy_activation_benchmark(trials=args.trials, seed=args.seed)
    write_noisy_activation_artifacts(records, args.output_dir)
    print(json.dumps(summarize_noisy_activation(records), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
