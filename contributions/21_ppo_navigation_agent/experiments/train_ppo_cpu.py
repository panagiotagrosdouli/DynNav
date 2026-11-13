#!/usr/bin/env python3
"""Train the real CPU PPO update and retain paired, held-out toy-environment outcomes."""
from __future__ import annotations
import argparse
import copy
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ppo_nav_agent import NavEnv, PPOAgent, PPOConfig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--eval-seeds", type=int, default=16)
    args = parser.parse_args()
    if args.updates < 1 or args.eval_seeds < 2:
        parser.error("positive updates and at least two held-out seeds required")
    cfg = PPOConfig(obs_dim=13, action_dim=2, hidden_dim=32, rollout_len=128, batch_size=64)
    agent = PPOAgent(cfg)
    agent._rng = np.random.default_rng(args.seed)
    initial = copy.deepcopy(agent.actor)
    before = agent.actor.l1.W.copy()
    log = agent.train(NavEnv(cfg, seed=args.seed), n_updates=args.updates)
    if np.array_equal(before, agent.actor.l1.W):
        raise RuntimeError("Training did not update actor parameters")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with (output / "training.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(log[0]))
        writer.writeheader()
        writer.writerows(log)
    weights = {}
    for family, network in [("actor", agent.actor), ("critic", agent.critic)]:
        for layer_name in ["l1", "l2", "out"]:
            layer = getattr(network, layer_name)
            for key in ["W", "b"]:
                weights[f"{family}_{layer_name}_{key}"] = getattr(layer, key)
    weights["actor_log_std"] = agent.actor.log_std
    np.savez(output / "checkpoint.npz", **weights)
    rows = []
    for seed in range(1000, 1000 + args.eval_seeds):
        if seed == args.seed:
            raise ValueError("Training and held-out seed overlap")
        for policy in ["initial", "trained", "greedy"]:
            env = NavEnv(cfg, seed=seed)
            obs = env.reset()
            total_reward = 0.0
            collisions = 0
            for step in range(env.max_steps):
                if policy == "greedy":
                    direction = env.goal_pos - env.robot_pos
                    action = direction / (np.linalg.norm(direction) + 1e-8)
                else:
                    actor = initial if policy == "initial" else agent.actor
                    action = actor.forward(obs)[0]
                obs, reward, done, info = env.step(action)
                total_reward += reward
                collisions += info["min_obs_dist"] < 0.4
                if done:
                    break
            rows.append(
                dict(
                    seed=seed,
                    policy=policy,
                    success=info["dist_goal"] < 0.5,
                    steps=step + 1,
                    return_sum=total_reward,
                    collision_steps=collisions,
                    final_goal_distance=info["dist_goal"],
                )
            )
    with (output / "heldout.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    for policy in ["initial", "trained", "greedy"]:
        selected = [r for r in rows if r["policy"] == policy]
        summary[policy] = dict(
            successes=int(sum(r["success"] for r in selected)),
            trials=len(selected),
            mean_return=float(np.mean([r["return_sum"] for r in selected])),
            collision_steps=int(sum(r["collision_steps"] for r in selected)),
        )
    metadata = dict(
        evidence="synthetic_toy_environment_actual_gradient_training",
        seed=args.seed,
        heldout_seeds=list(range(1000, 1000 + args.eval_seeds)),
        configuration=asdict(cfg),
        optimizer="CPU PyTorch autograd, clipped Gaussian PPO surrogate, SGD, global gradient clipping",
        source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        source_sha256=hashlib.sha256(
            (Path(__file__).resolve().parents[1] / "ppo_nav_agent.py").read_bytes()
        ).hexdigest(),
        checkpoint_sha256=hashlib.sha256((output / "checkpoint.npz").read_bytes()).hexdigest(),
        updates=args.updates,
        hardware=platform.platform(),
        summary=summary,
        limitation="Small toy environment and one training seed; not ROS, robot efficacy or generalization. "
        "Held-out outcomes are paired by seed; checkpoint usefulness is not presumed.",
    )
    (output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
