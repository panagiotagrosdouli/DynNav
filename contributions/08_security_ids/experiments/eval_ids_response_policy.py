"""IDS response-policy benchmark for Contribution 08.

This experiment feeds synthetic innovation-monitor outputs into the IDS response
policy and records the resulting trust score and planner mitigation.

Run from the repository root:

    python contributions/08_security_ids/experiments/eval_ids_response_policy.py

Output:

    contributions/08_security_ids/results/c08_ids_response_policy.csv
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

from ids_response_policy import classify_ids_response  # noqa: E402

RESULTS_DIR = Path("contributions/08_security_ids/results")
DEFAULT_OUT = RESULTS_DIR / "c08_ids_response_policy.csv"


def scenarios() -> list[dict[str, float | int | bool | str]]:
    return [
        {"scenario": "normal_noise", "d2": 2.1, "thr": 9.2, "flag_rate": 0.02, "triggered": False, "streak": 0},
        {"scenario": "elevated_innovation", "d2": 6.4, "thr": 9.2, "flag_rate": 0.08, "triggered": False, "streak": 1},
        {"scenario": "single_large_spike", "d2": 12.0, "thr": 9.2, "flag_rate": 0.10, "triggered": False, "streak": 1},
        {"scenario": "gradual_spoofing", "d2": 9.8, "thr": 9.2, "flag_rate": 0.32, "triggered": True, "streak": 3},
        {"scenario": "sustained_attack", "d2": 28.0, "thr": 9.2, "flag_rate": 0.55, "triggered": True, "streak": 7},
    ]


def write_csv(path: Path, rows: list[dict[str, float | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C08 IDS response-policy benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows: list[dict[str, float | bool | str]] = []
    for scenario in scenarios():
        response = classify_ids_response(scenario)
        rows.append({**scenario, **response.to_dict()})

    write_csv(args.out, rows)
    print(f"Saved C08 IDS response-policy benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<20} severity={row['severity']:<8} "
            f"mitigation={row['mitigation']:<16} trust={float(row['trust_score']):.3f}"
        )


if __name__ == "__main__":
    main()
