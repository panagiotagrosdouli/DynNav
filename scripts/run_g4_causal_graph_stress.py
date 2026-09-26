from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.causal_graph_stress_benchmark import (
    run_causal_graph_stress_benchmark,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the G4 randomized trigger-graph stress benchmark."
    )
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260926)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/research_gap_program/g4_causal_graph_stress.json"
        ),
    )
    args = parser.parse_args()

    result = run_causal_graph_stress_benchmark(
        repetitions=args.repetitions,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
