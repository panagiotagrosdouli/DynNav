from __future__ import annotations

import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"
TAU_CSV = RESULTS / "irreversibility_tau_sweep.csv"
SAFE_CSV = RESULTS / "irreversibility_safe_mode_sweep.csv"
RETURN_CSV = RESULTS / "returnability_mu_sweep.csv"
OUT_CSV = RESULTS / "c04_returnability_summary.csv"
OUT_MD = RESULTS / "c04_returnability_summary.md"


def load_rows(path: Path):
    with path.open("r", newline="") as f:
        return list(csv.DictReader(f))


def f(row, key, default=0.0):
    value = row.get(key, "")
    if value == "" or value is None:
        return default
    return float(value)


def success_rate(rows):
    if not rows:
        return 0.0
    return sum(int(float(r.get("success", 0))) for r in rows) / len(rows)


def min_success_tau(rows):
    successes = [r for r in rows if int(float(r.get("success", 0))) == 1]
    if not successes:
        return None
    return min(f(r, "tau") for r in successes)


def main():
    tau_rows = load_rows(TAU_CSV)
    safe_rows = load_rows(SAFE_CSV)
    return_rows = load_rows(RETURN_CSV)

    tau_success = success_rate(tau_rows)
    safe_success = success_rate(safe_rows)
    return_success = success_rate(return_rows)
    tau_min = min_success_tau(tau_rows)

    relaxed = [r for r in safe_rows if r.get("mode") == "SAFE_RELAX_TAU"]
    normal = [r for r in safe_rows if r.get("mode") == "NORMAL"]
    avg_gap = sum(f(r, "tau_gap") for r in relaxed) / len(relaxed) if relaxed else 0.0

    first_safe = safe_rows[0]
    first_return = return_rows[0]
    last_return = return_rows[-1]

    summary = {
        "tau_sweep_n": len(tau_rows),
        "tau_sweep_success_rate": tau_success,
        "min_feasible_tau": tau_min if tau_min is not None else "",
        "safe_mode_n": len(safe_rows),
        "safe_mode_success_rate": safe_success,
        "safe_mode_relaxed_cases": len(relaxed),
        "safe_mode_normal_cases": len(normal),
        "safe_mode_mean_tau_gap": avg_gap,
        "safe_mode_path_len": f(first_safe, "path_len"),
        "safe_mode_mean_I_on_path": f(first_safe, "mean_I_on_path"),
        "safe_mode_max_I_on_path": f(first_safe, "max_I_on_path"),
        "returnability_mu_n": len(return_rows),
        "returnability_success_rate": return_success,
        "returnability_meanR_mu0": f(first_return, "meanR"),
        "returnability_meanR_max_mu": f(last_return, "meanR"),
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    lines = [
        "# C04 Returnability and Irreversibility Summary",
        "",
        f"- Tau sweep success rate: {tau_success:.3f}",
        f"- Minimum feasible tau: {summary['min_feasible_tau']}",
        f"- Safe-mode success rate: {safe_success:.3f}",
        f"- Safe-mode relaxed cases: {len(relaxed)} / {len(safe_rows)}",
        f"- Mean tau relaxation gap: {avg_gap:.4f}",
        f"- Safe-mode path length: {summary['safe_mode_path_len']:.0f}",
        f"- Mean irreversibility on safe-mode path: {summary['safe_mode_mean_I_on_path']:.4f}",
        f"- Max irreversibility on safe-mode path: {summary['safe_mode_max_I_on_path']:.4f}",
        f"- Returnability sweep success rate: {return_success:.3f}",
        f"- Returnability meanR at mu=0: {summary['returnability_meanR_mu0']:.4f}",
        f"- Returnability meanR at largest mu: {summary['returnability_meanR_max_mu']:.4f}",
        "",
        "## Interpretation",
        "",
        "The hard irreversibility threshold admits paths only above the minimum feasible tau, while safe mode preserves feasibility by relaxing tau to the smallest viable threshold. This provides an explicit recoverability mechanism instead of silently failing when the nominal threshold is too strict.",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(f"[INFO] Wrote {OUT_CSV}")
    print(f"[INFO] Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
