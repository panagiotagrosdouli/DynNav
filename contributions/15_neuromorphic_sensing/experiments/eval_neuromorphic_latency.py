"""Neuromorphic latency benchmark for Contribution 15.

This experiment compares an event/SNN obstacle detector with a simple frame-based
baseline on synthetic moving-obstacle sequences.

Run from the repository root:

    python contributions/15_neuromorphic_sensing/experiments/eval_neuromorphic_latency.py

Output:

    contributions/15_neuromorphic_sensing/results/c15_neuromorphic_latency.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from neuromorphic_benchmark import (  # noqa: E402
    evaluate_event_detector,
    evaluate_frame_baseline,
    moving_obstacle_frames,
)

RESULTS_DIR = Path("contributions/15_neuromorphic_sensing/results")
DEFAULT_OUT = RESULTS_DIR / "c15_neuromorphic_latency.csv"


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C15 event-camera latency benchmark.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    scenarios = [
        ("slow_obstacle", 3),
        ("medium_obstacle", 6),
        ("fast_obstacle", 10),
    ]
    rows: list[dict[str, float | int | bool | str]] = []
    for name, speed in scenarios:
        frames = moving_obstacle_frames(speed_px_per_frame=speed)
        for metrics in [evaluate_event_detector(frames), evaluate_frame_baseline(frames)]:
            rows.append({"scenario": name, "speed_px_per_frame": speed, **metrics.to_dict()})

    write_csv(args.out, rows)
    print(f"Saved C15 neuromorphic latency benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['scenario']:<16} {row['method']:<15} latency_us={float(row['latency_us']):.1f} "
            f"detected={row['detected']} events={row['n_events']} max_score={float(row['max_score']):.3f}"
        )


if __name__ == "__main__":
    main()
