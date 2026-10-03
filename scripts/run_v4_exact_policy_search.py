from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.v4_exact_policy_search import (
    run_exact_policy_search,
    summarize_exact_policy_search,
    write_exact_policy_search_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run development-only exact-vs-receding V4 adversarial search."
    )
    parser.add_argument("--candidates", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026100305)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/v4_exact_policy_search"),
    )
    args = parser.parse_args()

    records = run_exact_policy_search(
        candidates=args.candidates,
        seed=args.seed,
    )
    write_exact_policy_search_artifacts(records, args.output_dir)
    print(
        json.dumps(
            summarize_exact_policy_search(records),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
