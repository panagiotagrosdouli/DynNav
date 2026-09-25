from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.risk_budget_replication import run_risk_budget_replication


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-seed post-V1 G3 risk-budget replication.")
    parser.add_argument("--opportunities", type=int, default=1000)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument(
        "--output",
        default="results/research_gap_program/risk_budget_replication.json",
    )
    args = parser.parse_args()
    result = run_risk_budget_replication(
        opportunities=args.opportunities,
        repetitions=args.repetitions,
        seed=args.seed,
    )
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
