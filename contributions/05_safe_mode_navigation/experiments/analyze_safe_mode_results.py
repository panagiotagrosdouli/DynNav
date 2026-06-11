"""
analyze_safe_mode_results.py

Διαβάζει το multi_robot_safe_mode_results.csv και
υπολογίζει συνοπτικά στατιστικά για:

- NORMAL_POLICY
- SAFE_MODE_POLICY

με βάση total_distance, total_risk, max_risk, total_cost.
"""

import csv
from collections import defaultdict
import numpy as np


from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUT_CSV = BASE / "results" / "multi_robot_safe_mode_results.csv"

def load_results(path: str):
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def summarize_by_policy(rows):
    """
    Ομαδοποίηση ανά policy.
    Παρότι το CSV έχει μία γραμμή ανά robot ανά step,
    εδώ θα κάνουμε aggregate ανά (step, policy) ώστε να
    μετράμε κάθε mission μία φορά.
    """

    # key: (step, policy) -> metrics
    missions = {}

    for r in rows:
        step = int(r["step"])
        policy = r["policy"]
        key = (step, policy)

        # τα mission-level metrics είναι ίδια για όλα τα robots σε ίδιο step
        if key not in missions:
            missions[key] = {
                "total_distance": float(r["total_distance"]),
                "total_risk": float(r["total_risk"]),
                "max_risk": float(r["max_risk"]),
                "total_cost": float(r["total_cost"]),
            }

    # τώρα κάνουμε aggregate ανά policy
    per_policy = defaultdict(lambda: defaultdict(list))

    for (step, policy), m in missions.items():
        per_policy[policy]["total_distance"].append(m["total_distance"])
        per_policy[policy]["total_risk"].append(m["total_risk"])
        per_policy[policy]["max_risk"].append(m["max_risk"])
        per_policy[policy]["total_cost"].append(m["total_cost"])

    return per_policy


def print_summary(per_policy):
    print("Analysis of multi_robot_safe_mode_results.csv:\n")

    for policy, metrics_dict in per_policy.items():
        print(f"=== Policy: {policy} ===")
        for metric_name, values in metrics_dict.items():
            arr = np.array(values, dtype=float)
            mean = float(arr.mean())
            std = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
            print(f" {metric_name:>14}: mean = {mean:.3f}, std = {std:.3f}")
        print()


def write_summary_outputs(per_policy):
    out_dir = BASE / "results"
    out_csv = out_dir / "c05_safe_mode_summary.csv"
    out_md = out_dir / "c05_safe_mode_summary.md"

    summary = {}

    for policy, metrics_dict in per_policy.items():
        for metric_name, values in metrics_dict.items():
            arr = np.array(values, dtype=float)
            summary[f"{policy}_{metric_name}_mean"] = float(arr.mean())
            summary[f"{policy}_{metric_name}_std"] = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0

    normal_risk = summary["NORMAL_POLICY_total_risk_mean"]
    safe_risk = summary["SAFE_MODE_POLICY_total_risk_mean"]
    normal_max = summary["NORMAL_POLICY_max_risk_mean"]
    safe_max = summary["SAFE_MODE_POLICY_max_risk_mean"]
    normal_dist = summary["NORMAL_POLICY_total_distance_mean"]
    safe_dist = summary["SAFE_MODE_POLICY_total_distance_mean"]
    normal_cost = summary["NORMAL_POLICY_total_cost_mean"]
    safe_cost = summary["SAFE_MODE_POLICY_total_cost_mean"]

    summary["risk_reduction_pct"] = 100.0 * (normal_risk - safe_risk) / normal_risk
    summary["max_risk_reduction_pct"] = 100.0 * (normal_max - safe_max) / normal_max
    summary["distance_increase_pct"] = 100.0 * (safe_dist - normal_dist) / normal_dist
    summary["cost_increase_pct"] = 100.0 * (safe_cost - normal_cost) / normal_cost

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    with open(out_md, "w") as f:
        f.write("# C05 Safe-Mode Navigation Summary\n\n")
        f.write(f"- Normal total risk: {normal_risk:.3f}\n")
        f.write(f"- Safe-mode total risk: {safe_risk:.3f}\n")
        f.write(f"- Risk reduction: {summary['risk_reduction_pct']:.2f}%\n")
        f.write(f"- Normal max risk: {normal_max:.3f}\n")
        f.write(f"- Safe-mode max risk: {safe_max:.3f}\n")
        f.write(f"- Max-risk reduction: {summary['max_risk_reduction_pct']:.2f}%\n")
        f.write(f"- Distance increase: {summary['distance_increase_pct']:.2f}%\n")
        f.write(f"- Cost increase: {summary['cost_increase_pct']:.2f}%\n\n")
        f.write("## Interpretation\n\n")
        f.write(
            "Safe mode reduces cumulative and peak risk relative to normal navigation, "
            "but does so through more conservative behavior that increases distance and cost.\n"
        )

    print(f"[INFO] Wrote {out_csv}")
    print(f"[INFO] Wrote {out_md}")


def main():
    rows = load_results(INPUT_CSV)
    if not rows:
        print("No rows found in CSV.")
        return

    per_policy = summarize_by_policy(rows)
    print_summary(per_policy)
    write_summary_outputs(per_policy)

if __name__ == "__main__":
    main()
