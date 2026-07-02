"""Policy evaluation utilities for Contribution 21.

The PPO module provides a training skeleton. This evaluator measures navigation
outcomes that matter for robot policy learning:

- success rate,
- collision rate,
- mean episode reward,
- minimum obstacle distance,
- final goal distance,
- shield intervention rate.

It compares a PPO actor, a greedy goal-directed baseline, and a shielded PPO
variant that clips risky actions when an obstacle is too close.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np

from ppo_nav_agent import NavEnv, PPOAgent, PPOConfig


@dataclass(frozen=True)
class PolicyEvalResult:
    policy_name: str
    n_episodes: int
    success_rate: float
    collision_rate: float
    mean_reward: float
    mean_episode_length: float
    mean_min_obstacle_distance: float
    mean_final_goal_distance: float
    shield_intervention_rate: float

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def greedy_goal_action(env: NavEnv, speed: float = 0.8) -> np.ndarray:
    direction = env.goal_pos - env.robot_pos
    norm = np.linalg.norm(direction) + 1e-9
    return speed * direction / norm


def shield_action(action: np.ndarray, env: NavEnv, min_safe_dist: float = 0.8) -> tuple[np.ndarray, bool]:
    if not env.obstacles:
        return action, False
    nearest = min(env.obstacles, key=lambda o: np.linalg.norm(env.robot_pos - o))
    vec_from_obs = env.robot_pos - nearest
    dist = float(np.linalg.norm(vec_from_obs))
    if dist >= min_safe_dist:
        return action, False
    avoid = vec_from_obs / (dist + 1e-9)
    corrected = 0.5 * action + 0.7 * avoid
    return np.clip(corrected, -1.0, 1.0), True


def evaluate_policy(
    policy_name: str,
    action_fn: Callable[[np.ndarray, NavEnv], np.ndarray],
    cfg: PPOConfig | None = None,
    n_episodes: int = 30,
    max_steps: int = 120,
    seed: int = 123,
) -> PolicyEvalResult:
    cfg = cfg or PPOConfig(obs_dim=14, rollout_len=128)
    env = NavEnv(cfg)
    env.max_steps = max_steps
    env._rng = np.random.default_rng(seed)

    successes = 0
    collisions = 0
    rewards: list[float] = []
    lengths: list[int] = []
    min_dists: list[float] = []
    final_dists: list[float] = []
    interventions = 0
    total_steps = 0

    for _ in range(n_episodes):
        obs = env.reset()
        ep_reward = 0.0
        ep_min_dist = float("inf")
        for step in range(max_steps):
            action = action_fn(obs, env)
            if policy_name.endswith("shielded"):
                action, intervened = shield_action(action, env)
                interventions += int(intervened)
            next_obs, reward, done, info = env.step(action)
            ep_reward += reward
            ep_min_dist = min(ep_min_dist, float(info["min_obs_dist"]))
            obs = next_obs
            total_steps += 1
            if float(info["min_obs_dist"]) < 0.4:
                collisions += 1
                done = True
            if float(info["dist_goal"]) < 0.5:
                successes += 1
                done = True
            if done:
                lengths.append(step + 1)
                break
        else:
            lengths.append(max_steps)
        rewards.append(float(ep_reward))
        min_dists.append(float(ep_min_dist))
        final_dists.append(float(np.linalg.norm(env.robot_pos - env.goal_pos)))

    return PolicyEvalResult(
        policy_name=policy_name,
        n_episodes=n_episodes,
        success_rate=float(successes / n_episodes),
        collision_rate=float(collisions / n_episodes),
        mean_reward=float(np.mean(rewards)),
        mean_episode_length=float(np.mean(lengths)),
        mean_min_obstacle_distance=float(np.mean(min_dists)),
        mean_final_goal_distance=float(np.mean(final_dists)),
        shield_intervention_rate=float(interventions / max(1, total_steps)),
    )


def make_policy_actions(agent: PPOAgent):
    def ppo_action(obs: np.ndarray, env: NavEnv) -> np.ndarray:
        mean, _ = agent.actor.forward(obs)
        return np.clip(mean, -1.0, 1.0)

    def shielded_ppo_action(obs: np.ndarray, env: NavEnv) -> np.ndarray:
        return ppo_action(obs, env)

    def greedy_action(obs: np.ndarray, env: NavEnv) -> np.ndarray:
        return np.clip(greedy_goal_action(env), -1.0, 1.0)

    return ppo_action, shielded_ppo_action, greedy_action
