from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from dynnav.research_pipeline import PLANNERS, load_config, run_pipeline


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run DynNav planner benchmark suite.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--out-dir", default="results/benchmarks")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)

    base = load_config(args.config)
    root = Path(args.out_dir)
    rows = []
    for planner in PLANNERS:
        cfg = dict(base)
        cfg["planner"] = planner
        cfg["output_dir"] = str(root / planner)
        metrics = run_pipeline(cfg, smoke=args.smoke)
        rows.append(metrics)

    metrics_dir = Path("results/metrics")
    reports_dir = Path("results/reports")
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    with (metrics_dir / "benchmark_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (reports_dir / "benchmark_report.md").write_text(
        "# Benchmark Report\n\nSynthetic deterministic benchmark. No state-of-the-art or real-world claim.\n\n```json\n"
        + json.dumps(rows, indent=2)
        + "\n```\n"
    )
    print("Benchmark outputs saved to results/metrics/benchmark_summary.csv and results/reports/benchmark_report.md")


if __name__ == "__main__":
    main()
