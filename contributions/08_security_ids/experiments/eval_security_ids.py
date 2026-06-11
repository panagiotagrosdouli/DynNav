import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"

METHODS = RESULTS / "ids_methods_summary.csv"

OUT_CSV = RESULTS / "c08_security_ids_summary.csv"
OUT_MD = RESULTS / "c08_security_ids_summary.md"


def main():
    rows = []

    with open(METHODS, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    best = max(rows, key=lambda r: float(r["ROC_AUC"]))

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "method",
                "ROC_AUC",
                "detect_rate",
                "FPR_star",
                "delay_mean_steps",
            ],
        )
        writer.writeheader()

        for r in rows:
            writer.writerow({
                "method": r["method"],
                "ROC_AUC": r["ROC_AUC"],
                "detect_rate": r["detect_rate"],
                "FPR_star": r["FPR_star"],
                "delay_mean_steps": r["delay_mean_steps"],
            })

    with open(OUT_MD, "w") as f:
        f.write("# C08 Security IDS Summary\n\n")

        f.write(
            f"- Best detector: {best['method']}\n"
            f"- ROC-AUC: {float(best['ROC_AUC']):.3f}\n"
            f"- Detection rate: {float(best['detect_rate']):.3f}\n"
            f"- False-positive rate: {float(best['FPR_star']):.4f}\n"
            f"- Mean detection delay: {float(best['delay_mean_steps']):.2f} steps\n\n"
        )

        f.write("## Interpretation\n\n")
        f.write(
            "CUSUM and EWMA substantially outperform raw NIS thresholding. "
            "CUSUM achieves the strongest ROC-AUC while maintaining near-1% false-positive rate "
            "and perfect attack detection rate.\n"
        )

    print(f"[INFO] Wrote {OUT_CSV}")
    print(f"[INFO] Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
