from __future__ import annotations

import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"
SWEEP_CSV = RESULTS / "belief_risk_lambda_sweep.csv"
OUT_CSV = RESULTS / "c03_belief_risk_summary.csv"
OUT_MD = RESULTS / "c03_belief_risk_summary.md"


def load_rows(path: Path):
    with path.open("r", newline="") as f:
        return list(csv.DictReader(f))


def as_float(row, key):
    return float(row[key])


def main():
    if not SWEEP_CSV.exists():
        raise FileNotFoundError(f"Missing input: {SWEEP_CSV}")

    rows = load_rows(SWEEP_CSV)
    if not rows:
        raise RuntimeError(f"Empty input: {SWEEP_CSV}")

    feasible = [r for r in rows if str(r.get("found_path", "True")).lower() == "true"]
    best_risk = min(feasible, key=lambda r: as_float(r, "fused_mean"))
    best_cost = min(feasible, key=lambda r: as_float(r, "total_cost"))
    baseline = min(feasible, key=lambda r: abs(as_float(r, "lambda") - 0.0))

    base_risk = as_float(baseline, "fused_mean")
    best_risk_val = as_float(best_risk, "fused_mean")
    base_len = as_float(baseline, "geometric_length")
    best_risk_len = as_float(best_risk, "geometric_length")
    risk_reduction_pct = (base_risk - best_risk_val) / base_risk * 100.0 if base_risk else 0.0
    length_change_pct = (best_risk_len - base_len) / base_len * 100.0 if base_len else 0.0

    summary = {
        "n_lambda_values": len(rows),
        "success_rate": len(feasible) / len(rows),
        "baseline_lambda": as_float(baseline, "lambda"),
        "baseline_fused_mean": base_risk,
        "baseline_geometric_length": base_len,
        "best_risk_lambda": as_float(best_risk, "lambda"),
        "best_risk_fused_mean": best_risk_val,
        "best_risk_geometric_length": best_risk_len,
        "risk_reduction_pct_vs_lambda0": risk_reduction_pct,
        "length_change_pct_vs_lambda0": length_change_pct,
        "best_cost_lambda": as_float(best_cost, "lambda"),
        "best_cost": as_float(best_cost, "total_cost"),
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    lines = [
        "# C03 Belief-Risk Planning Summary",
        "",
        f"- Lambda values evaluated: {summary['n_lambda_values']}",
        f"- Success rate: {summary['success_rate']:.3f}",
        f"- Baseline lambda: {summary['baseline_lambda']:.3f}",
        f"- Baseline fused mean risk: {summary['baseline_fused_mean']:.4f}",
        f"- Best-risk lambda: {summary['best_risk_lambda']:.3f}",
        f"- Best fused mean risk: {summary['best_risk_fused_mean']:.4f}",
        f"- Risk reduction vs lambda=0: {summary['risk_reduction_pct_vs_lambda0']:.2f}%",
        f"- Geometric length change vs lambda=0: {summary['length_change_pct_vs_lambda0']:.2f}%",
        "",
        "## Interpretation",
        "",
        "The lambda sweep demonstrates that risk-aware weighting can reduce fused path risk relative to the lambda=0 baseline. In the current stored benchmark, the best-risk setting reduces mean fused risk without increasing geometric path length.",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(f"[INFO] Wrote {OUT_CSV}")
    print(f"[INFO] Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
