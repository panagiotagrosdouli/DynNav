"""Risk-map quality benchmark for Contribution 12.

This benchmark compares deterministic and probabilistic occupancy risk maps
against synthetic future occupancy outcomes.

Run from the repository root:

    python contributions/12_diffusion_occupancy/experiments/eval_risk_map_quality.py

Output:

    contributions/12_diffusion_occupancy/results/c12_risk_map_quality.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from risk_map_evaluator import evaluate_risk_map  # noqa: E402

RESULTS_DIR = Path("contributions/12_diffusion_occupancy/results")
DEFAULT_OUT = RESULTS_DIR / "c12_risk_map_quality.csv"


def make_future_occupancy(seed: int, h: int = 32, w: int = 32) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]
    blob1 = ((x - 10) ** 2 + (y - 15) ** 2) < 24
    blob2 = ((x - 22) ** 2 + (y - 18) ** 2) < 16
    noise = rng.random((h, w)) < 0.015
    return np.logical_or.reduce([blob1, blob2, noise]).astype(float)


def blur_like_probability(observed: np.ndarray, rng: np.random.Generator, noise_scale: float) -> np.ndarray:
    # Lightweight pseudo-blur without scipy: average with shifted copies.
    p = observed.copy().astype(float)
    for dy, dx in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]:
        p += np.roll(np.roll(observed, dy, axis=0), dx, axis=1)
    p = p / 7.0
    p = 0.08 + 0.84 * p
    p += rng.normal(0.0, noise_scale, size=p.shape)
    return np.clip(p, 0.01, 0.99)


def scenarios(n: int) -> list[dict[str, np.ndarray | str]]:
    rows = []
    for i in range(n):
        observed = make_future_occupancy(i)
        rng = np.random.default_rng(100 + i)
        deterministic = np.clip(observed * 0.75 + 0.10 + rng.normal(0, 0.18, observed.shape), 0.01, 0.99)
        probabilistic = blur_like_probability(observed, rng, noise_scale=0.08)
        cvar = np.clip(probabilistic + 0.12 * (probabilistic > 0.35), 0.01, 0.99)
        rows.append({"scenario": f"future_{i:03d}", "observed": observed, "deterministic": deterministic, "probabilistic": probabilistic, "cvar": cvar})
    return rows


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C12 risk-map quality benchmark.")
    parser.add_argument("--n-scenarios", type=int, default=12)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    out_rows: list[dict[str, float | str]] = []
    for case in scenarios(args.n_scenarios):
        observed = case["observed"]
        for method in ["deterministic", "probabilistic"]:
            cvar = case["cvar"] if method == "probabilistic" else case[method]
            metrics = evaluate_risk_map(case[method], observed, cvar_map=cvar)
            out_rows.append({"scenario": case["scenario"], "method": method, **metrics.to_dict()})

    write_csv(args.out, out_rows)
    print(f"Saved C12 risk-map quality benchmark to {args.out}")
    for method in ["deterministic", "probabilistic"]:
        subset = [r for r in out_rows if r["method"] == method]
        mean_brier = sum(float(r["brier_score"]) for r in subset) / len(subset)
        mean_nll = sum(float(r["nll"]) for r in subset) / len(subset)
        print(f"{method:<14} mean_brier={mean_brier:.4f} mean_nll={mean_nll:.4f}")


if __name__ == "__main__":
    main()
