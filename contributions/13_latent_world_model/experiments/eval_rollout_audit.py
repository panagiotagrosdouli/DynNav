"""Imagined rollout audit benchmark for Contribution 13.

This benchmark evaluates candidate action sequences with rollout-level metrics:
imagined return, effort, terminal latent norm, recoverability proxy, and final
selection score.

Run from the repository root:

    python contributions/13_latent_world_model/experiments/eval_rollout_audit.py

Output:

    contributions/13_latent_world_model/results/c13_rollout_audit.csv
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

from latent_world_model import RSSM, RSSMConfig  # noqa: E402
from rollout_auditor import RolloutAuditConfig, audit_rollouts  # noqa: E402

RESULTS_DIR = Path("contributions/13_latent_world_model/results")
DEFAULT_OUT = RESULTS_DIR / "c13_rollout_audit.csv"


def sequence(value: tuple[float, float], horizon: int) -> list[np.ndarray]:
    return [np.asarray(value, dtype=float) for _ in range(horizon)]


def candidate_sequences(horizon: int) -> dict[str, list[np.ndarray]]:
    return {
        "cautious_forward": sequence((0.20, 0.00), horizon),
        "aggressive_forward": sequence((0.95, 0.00), horizon),
        "turning_probe": sequence((0.35, 0.55), horizon),
        "retreat_recover": sequence((-0.30, 0.00), horizon),
        "oscillatory_uncertain": [np.asarray(((-1) ** i * 0.8, 0.65), dtype=float) for i in range(horizon)],
    }


def write_csv(path: Path, rows: list[dict[str, float | int | bool | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C13 latent world-model rollout audit benchmark.")
    parser.add_argument("--horizon", type=int, default=12)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    cfg = RSSMConfig(obs_dim=32, action_dim=2, latent_dim=12, hidden_dim=24, horizon=args.horizon)
    rssm = RSSM(cfg)
    h0 = np.zeros(cfg.hidden_dim)
    z0 = np.zeros(cfg.latent_dim)

    audit_cfg = RolloutAuditConfig(gamma=cfg.gamma, irreversibility_penalty=cfg.irreversibility_penalty)
    rows = [r.to_dict() for r in audit_rollouts(rssm, h0, z0, candidate_sequences(args.horizon), cfg=audit_cfg)]

    write_csv(args.out, rows)
    print(f"Saved C13 rollout audit benchmark to {args.out}")
    for row in rows:
        marker = "*" if row["selected"] else " "
        print(
            f"{marker} {row['sequence_name']:<22} score={float(row['final_score']):.3f} "
            f"return={float(row['imagined_return']):.3f} recoverability={float(row['recoverability_proxy']):.3f} "
            f"irreversible={row['irreversible']}"
        )


if __name__ == "__main__":
    main()
