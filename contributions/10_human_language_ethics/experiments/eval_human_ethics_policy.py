"""Human-aware ethics policy benchmark for Contribution 10.

This benchmark evaluates how ethical zones, human proximity, operator trust, and
language confidence are converted into planner actions.

Run from the repository root:

    python contributions/10_human_language_ethics/experiments/eval_human_ethics_policy.py

Output:

    contributions/10_human_language_ethics/results/c10_human_ethics_policy.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from human_ethics_policy import HumanEthicsContext, ZoneType, decide_human_ethics_policy  # noqa: E402

RESULTS_DIR = Path("contributions/10_human_language_ethics/results")
DEFAULT_OUT = RESULTS_DIR / "c10_human_ethics_policy.csv"


def scenarios() -> dict[str, HumanEthicsContext]:
    return {
        "normal_corridor": HumanEthicsContext(zone_type=ZoneType.NONE, distance_to_human_m=6.0, operator_trust=0.95, language_confidence=0.90),
        "human_nearby": HumanEthicsContext(zone_type=ZoneType.NONE, distance_to_human_m=1.8, operator_trust=0.90, language_confidence=0.90),
        "personal_space": HumanEthicsContext(zone_type=ZoneType.NONE, distance_to_human_m=0.8, operator_trust=0.90, language_confidence=0.90),
        "no_go_zone": HumanEthicsContext(zone_type=ZoneType.NO_GO, distance_to_human_m=5.0, operator_trust=0.90, language_confidence=0.90),
        "slow_zone": HumanEthicsContext(zone_type=ZoneType.SLOW_ZONE, distance_to_human_m=4.0, operator_trust=0.90, language_confidence=0.90),
        "announce_zone": HumanEthicsContext(zone_type=ZoneType.ANNOUNCE, distance_to_human_m=4.0, operator_trust=0.90, language_confidence=0.90),
        "low_operator_trust": HumanEthicsContext(zone_type=ZoneType.NONE, distance_to_human_m=5.0, operator_trust=0.20, language_confidence=0.90),
        "ambiguous_language": HumanEthicsContext(zone_type=ZoneType.NONE, distance_to_human_m=5.0, operator_trust=0.90, language_confidence=0.30),
        "soft_ethical_zone": HumanEthicsContext(zone_type=ZoneType.AVOID_IF_POSSIBLE, distance_to_human_m=4.0, operator_trust=0.90, language_confidence=0.90),
    }


def write_csv(path: Path, rows: list[dict[str, float | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C10 human-aware ethics policy benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows: list[dict[str, float | bool | str]] = []
    for name, context in scenarios().items():
        decision = decide_human_ethics_policy(context)
        rows.append(
            {
                "scenario": name,
                "zone_type": context.zone_type.value,
                "distance_to_human_m": context.distance_to_human_m,
                "operator_trust": context.operator_trust,
                "language_confidence": context.language_confidence,
                **decision.to_dict(),
            }
        )

    write_csv(args.out, rows)
    print(f"Saved C10 human ethics policy benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<22} action={row['action']:<18} "
            f"allowed={row['path_allowed']} speed={float(row['max_speed']):.2f} "
            f"confirm={row['requires_operator_confirmation']}"
        )


if __name__ == "__main__":
    main()
