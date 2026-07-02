"""PPO policy safety benchmark for Contribution 21.

This benchmark compares a PPO actor, a shielded PPO actor, and a greedy-goal
baseline using navigation outcome metrics.

Run from the repository root:

    python contributions/21_ppo_navigation_agent/experiments/eval_policy_safety.py

Output:

    contributions/21_ppo_navigation_agent/results/c21_policy_safety.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from ppo_nav_agent import PPOAgent, PPOConfig  # noqa: E402
from ppo_policy_evaluator import evaluate_policy, make_policy_actions  # noqa: E402

RESULTS_DIR = Path("contributions/21_ppo_navigation_agent/results")
DEFAULT_OUT = RESULTS_DIR / "c21_policy_safety.csv"


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="C21 PPO policy safety benchmark.")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    cfg = PPOConfig(obs_dim=14, rollout_len=128)
    agent = PPOAgent(cfg)
    ppo_action, shielded_action, greedy_action = make_policy_actions(agent)

    results = [
        evaluate_policy("ppo", ppo_action, cfg=cfg, n_episodes=args.episodes, seed=123),
        evaluate_policy("ppo_shielded", shielded_action, cfg=cfg, n_episodes=args.episodes, seed=123),
        evaluate_policy("greedy_goal", greedy_action, cfg=cfg, n_episodes=args.episodes, seed=123),
    ]
    rows = [r.to_dict() for r in results]
    write_csv(args.out, rows)

    print(f"Saved C21 policy safety benchmark to {args.out}")
    for row in rows:
        print(
            f"{row['policy_name']:<14} success={float(row['success_rate']):.3f} "
            f"collision={float(row['collision_rate']):.3f} reward={float(row['mean_reward']):.3f} "
            f"min_dist={float(row['mean_min_obstacle_distance']):.3f} shield_rate={float(row['shield_intervention_rate']):.3f}"
        )


if __name__ == "__main__":
    main()
