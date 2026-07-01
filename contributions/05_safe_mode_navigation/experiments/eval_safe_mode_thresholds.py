"""Threshold-sensitivity benchmark for Contribution 05.

This experiment evaluates safe-mode switching on synthetic risk traces. It is
intended to make the safe-mode controller auditable: we can measure how many
steps are spent in normal/safe/emergency states, how often replanning is
triggered, and whether the controller flickers under noisy risk.

Run from the repository root:

    python contributions/05_safe_mode_navigation/experiments/eval_safe_mode_thresholds.py

Output:

    contributions/05_safe_mode_navigation/results/c05_safe_mode_thresholds.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from safe_mode_controller import SafeModeConfig, SafeModeController, summarize_outputs  # noqa: E402

RESULTS_DIR = Path("contributions/05_safe_mode_navigation/results")
DEFAULT_OUT = RESULTS_DIR / "c05_safe_mode_thresholds.csv"


def risk_trace(kind: str, n_steps: int) -> list[float]:
    if kind == "nominal_noise":
        return [0.30 + 0.06 * math.sin(i / 3.0) for i in range(n_steps)]
    if kind == "temporary_hazard":
        values = []
        for i in range(n_steps):
            if 10 <= i <= 18:
                values.append(0.78 + 0.04 * math.sin(i))
            else:
                values.append(0.32 + 0.05 * math.sin(i / 4.0))
        return values
    if kind == "critical_spike":
        values = [0.30 + 0.04 * math.sin(i / 5.0) for i in range(n_steps)]
        values[12] = 0.98
        values[13] = 0.96
        values[14] = 0.82
        return values
    if kind == "chattering_risk":
        return [0.66 + 0.08 * math.sin(i * 1.7) for i in range(n_steps)]
    raise ValueError(f"Unknown trace kind: {kind}")


def evaluate_trace(kind: str, cfg: SafeModeConfig, n_steps: int) -> dict[str, float | int | str]:
    controller = SafeModeController(cfg)
    outputs = [controller.update(r) for r in risk_trace(kind, n_steps)]
    summary = summarize_outputs(outputs)
    return {
        "trace": kind,
        "risk_on_threshold": cfg.risk_on_threshold,
        "risk_off_threshold": cfg.risk_off_threshold,
        "critical_threshold": cfg.critical_threshold,
        "activation_steps_required": cfg.activation_steps_required,
        "recovery_steps_required": cfg.recovery_steps_required,
        "cooldown_steps": cfg.cooldown_steps,
        **summary,
    }


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C05 safe-mode threshold sensitivity benchmark.")
    parser.add_argument("--n-steps", type=int, default=40)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    configs = [
        SafeModeConfig(risk_on_threshold=0.65, risk_off_threshold=0.40, activation_steps_required=1, recovery_steps_required=2, cooldown_steps=0),
        SafeModeConfig(risk_on_threshold=0.70, risk_off_threshold=0.45, activation_steps_required=2, recovery_steps_required=3, cooldown_steps=2),
        SafeModeConfig(risk_on_threshold=0.75, risk_off_threshold=0.50, activation_steps_required=3, recovery_steps_required=3, cooldown_steps=3),
    ]
    traces = ["nominal_noise", "temporary_hazard", "critical_spike", "chattering_risk"]

    rows: list[dict[str, float | int | str]] = []
    for cfg in configs:
        for trace in traces:
            rows.append(evaluate_trace(trace, cfg, args.n_steps))

    write_csv(args.out, rows)
    print(f"Saved C05 threshold benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['trace']} on={float(row['risk_on_threshold']):.2f}/off={float(row['risk_off_threshold']):.2f}: "
            f"safe={row['safe_mode_steps']}, emergency={row['emergency_stop_steps']}, "
            f"transitions={row['transitions']}, replans={row['replans']}"
        )


if __name__ == "__main__":
    main()
