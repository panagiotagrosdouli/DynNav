"""Calibration benchmark for Contribution 02.

This experiment demonstrates the distinction between informative uncertainty and
calibrated uncertainty. It supports the C02 research claim that uncertainty can be
useful for planning only after its probabilistic meaning is audited.

Run from the repository root:

    python contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py

Outputs:

    contributions/02_uncertainty_calibration/results/c02_calibration_benchmark.csv

The script can run without external datasets by generating a synthetic benchmark
with controlled miscalibration. It can also read a CSV with columns:

    prediction,target,sigma
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from uncertainty_calibrator import (  # noqa: E402
    GlobalScaleCalibrator,
    QuantileBinCalibrator,
    absolute_error,
    evaluate_calibration,
)

RESULTS_DIR = Path("contributions/02_uncertainty_calibration/results")
DEFAULT_OUT = RESULTS_DIR / "c02_calibration_benchmark.csv"


def generate_synthetic_data(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate prediction/target/sigma triples with realistic miscalibration.

    The synthetic model is intentionally imperfect:

    - uncertainty is monotonic with error scale,
    - but raw sigma is compressed and biased,
    - so rank correlation can be useful while Gaussian coverage is poor.
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(-3.0, 3.0, size=n)
    true_signal = np.sin(x) + 0.2 * x
    latent_difficulty = 0.25 + 0.75 * (np.abs(x) / 3.0)
    noise = rng.normal(0.0, latent_difficulty, size=n)
    prediction = true_signal + noise
    target = true_signal

    raw_sigma = 0.35 + 0.45 * latent_difficulty + rng.normal(0.0, 0.08, size=n)
    raw_sigma = np.maximum(raw_sigma, 0.05)
    return prediction, target, raw_sigma


def read_csv_dataset(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    predictions: list[float] = []
    targets: list[float] = []
    sigmas: list[float] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        required = {"prediction", "target", "sigma"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")
        for row in reader:
            predictions.append(float(row["prediction"]))
            targets.append(float(row["target"]))
            sigmas.append(float(row["sigma"]))
    return np.asarray(predictions), np.asarray(targets), np.asarray(sigmas)


def split_train_test(prediction: np.ndarray, target: np.ndarray, sigma: np.ndarray, train_fraction: float) -> tuple[np.ndarray, ...]:
    n = len(prediction)
    cut = int(round(n * train_fraction))
    if cut <= 0 or cut >= n:
        raise ValueError("train_fraction must leave at least one train and one test example.")
    return prediction[:cut], target[:cut], sigma[:cut], prediction[cut:], target[cut:], sigma[cut:]


def row_from_report(method: str, report) -> dict[str, float | int | str]:
    row = asdict(report)
    row["method"] = method
    return row


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        fieldnames = ["method", *[k for k in rows[0].keys() if k != "method"]]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C02 uncertainty calibration benchmark.")
    parser.add_argument("--input", type=Path, default=None, help="Optional CSV with prediction,target,sigma columns.")
    parser.add_argument("--n", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--train-fraction", type=float, default=0.5)
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if args.input is None:
        prediction, target, sigma = generate_synthetic_data(args.n, args.seed)
        dataset_name = "synthetic"
    else:
        prediction, target, sigma = read_csv_dataset(args.input)
        dataset_name = str(args.input)

    p_train, y_train, s_train, p_test, y_test, s_test = split_train_test(
        prediction, target, sigma, args.train_fraction
    )
    train_error = absolute_error(p_train, y_train)

    global_cal = GlobalScaleCalibrator().fit(train_error, s_train)
    bin_cal = QuantileBinCalibrator(n_bins=args.bins).fit(train_error, s_train)

    raw_report = evaluate_calibration(p_test, y_test, s_test, n_bins=args.bins)
    global_report = evaluate_calibration(p_test, y_test, global_cal.transform(s_test), n_bins=args.bins)
    bin_report = evaluate_calibration(p_test, y_test, bin_cal.transform(s_test), n_bins=args.bins)

    rows = [
        row_from_report("raw_sigma", raw_report),
        row_from_report(f"global_scale_{global_cal.scale:.4f}", global_report),
        row_from_report("quantile_bin_calibrated", bin_report),
    ]
    for row in rows:
        row["dataset"] = dataset_name
        row["train_fraction"] = args.train_fraction
        row["bins"] = args.bins

    write_csv(args.out, rows)
    print(f"Saved C02 calibration benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['method']}: ECE={float(row['ece_abs_error']):.4f}, "
            f"coverage@1σ={float(row['coverage_1sigma']):.3f}, "
            f"coverage@2σ={float(row['coverage_2sigma']):.3f}, "
            f"coverage@3σ={float(row['coverage_3sigma']):.3f}"
        )


if __name__ == "__main__":
    main()
