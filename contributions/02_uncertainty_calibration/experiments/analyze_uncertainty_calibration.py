import csv
import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
ERR_CSV = BASE / "phd_experiments" / "uncertainty_error_data.csv"
OUT_MD = BASE / "phd_experiments" / "uncertainty_calibration_summary.md"
OUT_CSV = BASE / "phd_experiments" / "uncertainty_calibration_metrics.csv"
PLOTS = BASE / "phd_experiments" / "uncertainty_plots"


def load_data():
    rows = []
    with ERR_CSV.open("r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "instance_id": int(r["instance_id"]),
                "x": int(r["state_x"]),
                "y": int(r["state_y"]),
                "h_star": float(r["h_star"]),
                "mu": float(r["mu"]),
                "sigma": float(r["sigma"]),
                "error": float(r["error"]),
                "abs_error": float(r["abs_error"]),
            })
    return rows


def pearson(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def rankdata(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = 0.5 * (i + j) + 1.0
        ranks[order[i:j + 1]] = avg_rank
        i = j + 1
    return ranks


def spearman(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if len(x) < 2:
        return float("nan")
    return pearson(rankdata(x), rankdata(y))


def gaussian_coverage(errors, sigmas, k):
    errors = np.asarray(errors, dtype=float)
    sigmas = np.asarray(sigmas, dtype=float)
    mask = np.isfinite(errors) & np.isfinite(sigmas) & (sigmas > 0)
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs(errors[mask]) <= k * sigmas[mask]))


def calibration_ece(sigmas, abs_errors, num_bins=10):
    sigmas = np.asarray(sigmas, dtype=float)
    abs_errors = np.asarray(abs_errors, dtype=float)
    mask = np.isfinite(sigmas) & np.isfinite(abs_errors)
    sigmas = sigmas[mask]
    abs_errors = abs_errors[mask]
    if len(sigmas) == 0:
        return float("nan")
    bins = np.linspace(sigmas.min(), sigmas.max(), num_bins + 1)
    total = len(sigmas)
    ece = 0.0
    for i in range(num_bins):
        if i == num_bins - 1:
            bin_mask = (sigmas >= bins[i]) & (sigmas <= bins[i + 1])
        else:
            bin_mask = (sigmas >= bins[i]) & (sigmas < bins[i + 1])
        if bin_mask.sum() == 0:
            continue
        mean_sigma = float(sigmas[bin_mask].mean())
        mean_abs = float(abs_errors[bin_mask].mean())
        ece += (bin_mask.sum() / total) * abs(mean_sigma - mean_abs)
    return float(ece)


def scatter_sigma_abs_error(sigmas, abs_errors, out_path):
    plt.figure()
    plt.scatter(sigmas, abs_errors, s=5, alpha=0.3)
    plt.xlabel("sigma (predictive std)")
    plt.ylabel("|error| = |mu - h*|")
    plt.title("Abs error vs predictive sigma")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def binned_calibration(sigmas, abs_errors, num_bins=10):
    sigmas = np.array(sigmas)
    abs_errors = np.array(abs_errors)
    finite_mask = np.isfinite(sigmas) & np.isfinite(abs_errors)
    sigmas = sigmas[finite_mask]
    abs_errors = abs_errors[finite_mask]
    if len(sigmas) == 0:
        return [], [], []
    bins = np.linspace(sigmas.min(), sigmas.max(), num_bins + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    mean_abs = []
    counts = []
    for i in range(num_bins):
        if i == num_bins - 1:
            mask = (sigmas >= bins[i]) & (sigmas <= bins[i + 1])
        else:
            mask = (sigmas >= bins[i]) & (sigmas < bins[i + 1])
        if mask.sum() == 0:
            mean_abs.append(float("nan"))
            counts.append(0)
        else:
            mean_abs.append(float(abs_errors[mask].mean()))
            counts.append(int(mask.sum()))
    return bin_centers, mean_abs, counts


def plot_binned_calibration(bin_centers, mean_abs, out_path):
    plt.figure()
    plt.plot(bin_centers, mean_abs, marker="o", label="mean |error|")
    plt.plot(bin_centers, bin_centers, linestyle="--", label="ideal: |error| = sigma")
    plt.xlabel("sigma bin center")
    plt.ylabel("mean |error|")
    plt.title("Binned calibration")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main():
    if not ERR_CSV.exists():
        print(f"[ERROR] {ERR_CSV} not found. Run the uncertainty error logging experiment first.")
        return

    PLOTS.mkdir(parents=True, exist_ok=True)
    data = load_data()
    sigmas = [r["sigma"] for r in data]
    abs_errors = [r["abs_error"] for r in data]
    errors = [r["error"] for r in data]

    scatter_sigma_abs_error(sigmas, abs_errors, PLOTS / "sigma_vs_abs_error.png")
    bin_centers, mean_abs, counts = binned_calibration(sigmas, abs_errors, num_bins=10)
    if len(bin_centers) > 0:
        plot_binned_calibration(bin_centers, mean_abs, PLOTS / "binned_calibration.png")

    valid_abs = [e for e in abs_errors if math.isfinite(e)]
    metrics = {
        "n_samples": len(data),
        "mae": float(sum(valid_abs) / len(valid_abs)) if valid_abs else float("nan"),
        "pearson_sigma_abs_error": pearson(sigmas, abs_errors),
        "spearman_sigma_abs_error": spearman(sigmas, abs_errors),
        "ece_sigma_abs_error": calibration_ece(sigmas, abs_errors, num_bins=10),
        "coverage_1sigma": gaussian_coverage(errors, sigmas, 1.0),
        "coverage_2sigma": gaussian_coverage(errors, sigmas, 2.0),
        "coverage_3sigma": gaussian_coverage(errors, sigmas, 3.0),
    }

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
        writer.writeheader()
        writer.writerow(metrics)

    lines = []
    lines.append("# Uncertainty Calibration Analysis\n")
    lines.append(f"- Total samples: {metrics['n_samples']}")
    lines.append(f"- Mean absolute error: {metrics['mae']:.4f}")
    lines.append(f"- Pearson corr(sigma, |error|): {metrics['pearson_sigma_abs_error']:.4f}")
    lines.append(f"- Spearman corr(sigma, |error|): {metrics['spearman_sigma_abs_error']:.4f}")
    lines.append(f"- ECE-style |mean sigma - mean |error||: {metrics['ece_sigma_abs_error']:.4f}")
    lines.append(f"- Coverage @ 1 sigma: {metrics['coverage_1sigma']:.4f}")
    lines.append(f"- Coverage @ 2 sigma: {metrics['coverage_2sigma']:.4f}")
    lines.append(f"- Coverage @ 3 sigma: {metrics['coverage_3sigma']:.4f}")
    lines.append("\n## Figures\n")
    lines.append("1. Scatter: |error| vs sigma -> `uncertainty_plots/sigma_vs_abs_error.png`")
    lines.append("2. Binned calibration plot -> `uncertainty_plots/binned_calibration.png`")
    lines.append("\n## Machine-readable metrics\n")
    lines.append("- `uncertainty_calibration_metrics.csv`")

    OUT_MD.write_text("\n".join(lines))
    print(f"[INFO] Wrote uncertainty calibration summary to {OUT_MD}")
    print(f"[INFO] Wrote uncertainty calibration metrics to {OUT_CSV}")


if __name__ == "__main__":
    main()
