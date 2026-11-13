"""
Contribution 21: PPO Navigation Agent
======================================
Proximal Policy Optimization (PPO) agent for autonomous navigation in
unknown environments. The agent learns a policy π(a|s) that maps occupancy
observations to velocity commands, with reward shaping from DynNav's
existing risk and safety modules.

Reward structure:
    r = r_progress - λ_risk * r_risk - λ_col * r_collision + r_goal

Research Question (RQ-PPO): Does RL-based navigation with risk-shaped
rewards outperform classical A* in highly dynamic environments?

References:
    Schulman et al. (2017) "Proximal Policy Optimization Algorithms"
    Mirowski et al. (2017) "Learning to Navigate in Complex Environments"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class PPOConfig:
    obs_dim: int = 84          # flattened observation (e.g. 8x8 local grid + goal dir)
    action_dim: int = 2        # (linear_vel, angular_vel) or discrete 5 actions
    hidden_dim: int = 128
    lr_actor: float = 3e-4
    lr_critic: float = 1e-3
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_eps: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    n_epochs: int = 4           # PPO update epochs per rollout
    batch_size: int = 64
    rollout_len: int = 512
    max_grad_norm: float = 0.5
    # Reward shaping
    lambda_risk: float = 0.5
    lambda_collision: float = 5.0
    goal_reward: float = 10.0
    step_penalty: float = -0.01


# ---------------------------------------------------------------------------
# NumPy inference networks, optimized through CPU PyTorch autograd in update()
# ---------------------------------------------------------------------------

class LinearLayer:
    """Single trainable linear layer with NumPy inference."""

    def __init__(self, in_d: int, out_d: int, activation: str = "relu", seed: int = 0):
        rng = np.random.default_rng(seed)
        self.W = rng.standard_normal((in_d, out_d)) * np.sqrt(2.0 / in_d)
        self.b = np.zeros(out_d)
        self.activation = activation

    def forward(self, x: np.ndarray) -> np.ndarray:
        out = x @ self.W + self.b
        if self.activation == "relu":
            return np.maximum(0, out)
        if self.activation == "tanh":
            return np.tanh(out)
        return out  # linear


class ActorNetwork:
    """Policy network: obs → action mean (continuous) or logits (discrete)."""

    def __init__(self, cfg: PPOConfig):
        self.l1 = LinearLayer(cfg.obs_dim, cfg.hidden_dim, "tanh", seed=1)
        self.l2 = LinearLayer(cfg.hidden_dim, cfg.hidden_dim, "tanh", seed=2)
        self.out = LinearLayer(cfg.hidden_dim, cfg.action_dim, "tanh", seed=3)
        self.log_std = np.full(cfg.action_dim, -0.5)   # learnable log std

    def forward(self, obs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x = self.l1.forward(obs)
        x = self.l2.forward(x)
        mean = self.out.forward(x)
        std = np.exp(self.log_std)
        return mean, std

    def sample(self, obs: np.ndarray,
               rng: np.random.Generator) -> tuple[np.ndarray, float]:
        mean, std = self.forward(obs)
        action = mean + std * rng.standard_normal(mean.shape)
        log_prob = float(np.sum(
            -0.5 * ((action - mean) / std) ** 2
            - np.log(std) - 0.5 * np.log(2 * np.pi)
        ))
        return action, log_prob


class CriticNetwork:
    """Value network: obs → V(s)."""

    def __init__(self, cfg: PPOConfig):
        self.l1 = LinearLayer(cfg.obs_dim, cfg.hidden_dim, "tanh", seed=4)
        self.l2 = LinearLayer(cfg.hidden_dim, cfg.hidden_dim, "tanh", seed=5)
        self.out = LinearLayer(cfg.hidden_dim, 1, "linear", seed=6)

    def forward(self, obs: np.ndarray) -> float:
        x = self.l1.forward(obs)
        x = self.l2.forward(x)
        return float(self.out.forward(x).squeeze())


# ---------------------------------------------------------------------------
# Rollout buffer
# ---------------------------------------------------------------------------

@dataclass
class RolloutBuffer:
    obs: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    log_probs: list = field(default_factory=list)
    rewards: list = field(default_factory=list)
    values: list = field(default_factory=list)
    dones: list = field(default_factory=list)

    def clear(self):
        self.obs.clear(); self.actions.clear(); self.log_probs.clear()
        self.rewards.clear(); self.values.clear(); self.dones.clear()

    def add(self, obs, action, log_prob, reward, value, done):
        self.obs.append(obs); self.actions.append(action)
        self.log_probs.append(log_prob); self.rewards.append(reward)
        self.values.append(value); self.dones.append(done)

    def compute_gae(self, last_value: float,
                    gamma: float, lam: float) -> tuple[np.ndarray, np.ndarray]:
        """Generalised Advantage Estimation."""
        T = len(self.rewards)
        advantages = np.zeros(T)
        gae = 0.0
        for t in reversed(range(T)):
            next_val = last_value if t == T - 1 else self.values[t + 1]
            delta = self.rewards[t] + gamma * next_val * (1 - self.dones[t]) - self.values[t]
            gae = delta + gamma * lam * (1 - self.dones[t]) * gae
            advantages[t] = gae
        returns = advantages + np.array(self.values)
        return advantages, returns


# ---------------------------------------------------------------------------
# Navigation environment (stub)
# ---------------------------------------------------------------------------

class NavEnv:
    """
    Minimal navigation environment compatible with PPO.
    Replace with Gazebo/ROS2 bridge for real-world deployment.
    """

    def __init__(self, cfg: PPOConfig, grid_size: int = 16, seed: int | None = None):
        self.cfg = cfg
        self.grid_size = grid_size
        self._rng = np.random.default_rng(seed)
        self.robot_pos = np.array([0.0, 0.0])
        self.goal_pos = np.array([5.0, 5.0])
        self.obstacles: list[np.ndarray] = []
        self.steps = 0
        self.max_steps = 200

    def reset(self) -> np.ndarray:
        self.robot_pos = self._rng.uniform(0, 2, 2)
        self.goal_pos = self._rng.uniform(6, 8, 2)
        n_obs = self._rng.integers(3, 8)
        self.obstacles = [self._rng.uniform(2, 7, 2) for _ in range(n_obs)]
        self.steps = 0
        return self._get_obs()

    def step(self, action: np.ndarray
             ) -> tuple[np.ndarray, float, bool, dict]:
        self.steps += 1
        self.robot_pos = np.clip(self.robot_pos + action * 0.3, 0, 10)

        dist_goal = float(np.linalg.norm(self.robot_pos - self.goal_pos))
        min_obs_dist = min(
            (np.linalg.norm(self.robot_pos - o) for o in self.obstacles),
            default=np.inf
        )

        # Reward shaping
        reward = self.cfg.step_penalty
        reward += 0.1 * (1.0 / (dist_goal + 0.1))        # progress
        reward -= self.cfg.lambda_risk * max(0, 1.5 - min_obs_dist)
        if min_obs_dist < 0.4:
            reward -= self.cfg.lambda_collision
        if dist_goal < 0.5:
            reward += self.cfg.goal_reward

        done = dist_goal < 0.5 or self.steps >= self.max_steps
        info = {"dist_goal": dist_goal, "min_obs_dist": min_obs_dist}
        return self._get_obs(), reward, done, info

    def _get_obs(self) -> np.ndarray:
        """Flat observation: robot_pos, goal_dir, goal_dist, 8-dir clearances."""
        goal_vec = self.goal_pos - self.robot_pos
        goal_dist = np.linalg.norm(goal_vec)
        goal_dir = goal_vec / (goal_dist + 1e-8)

        clearances = []
        for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            d = np.array([np.cos(angle), np.sin(angle)])
            min_c = min(
                (np.linalg.norm(self.robot_pos + d * t - o)
                 for o in self.obstacles for t in [0.5, 1.0, 1.5]),
                default=2.0
            )
            clearances.append(min(min_c, 2.0) / 2.0)

        obs = np.concatenate([
            self.robot_pos / 10.0,
            goal_dir,
            [goal_dist / 10.0],
            clearances,
        ])
        # Pad/truncate to obs_dim
        if len(obs) < self.cfg.obs_dim:
            obs = np.pad(obs, (0, self.cfg.obs_dim - len(obs)))
        return obs[:self.cfg.obs_dim].astype(np.float32)


# ---------------------------------------------------------------------------
# PPO Agent
# ---------------------------------------------------------------------------

class PPOAgent:
    """
    PPO agent for DynNav navigation.
    Uses NumPy inference and CPU PyTorch autograd for actual PPO SGD updates.
    """

    def __init__(self, cfg: PPOConfig | None = None):
        self.cfg = cfg or PPOConfig()
        self.actor = ActorNetwork(self.cfg)
        self.critic = CriticNetwork(self.cfg)
        self.buffer = RolloutBuffer()
        self._rng = np.random.default_rng(42)
        self.training_log: list[dict] = []
        self._last_value = 0.0

    def select_action(self, obs: np.ndarray) -> tuple[np.ndarray, float, float]:
        action, log_prob = self.actor.sample(obs, self._rng)
        value = self.critic.forward(obs)
        return action, log_prob, value

    def collect_rollout(self, env: NavEnv) -> dict:
        """Collect one rollout of rollout_len steps."""
        self.buffer.clear()
        obs = env.reset()
        ep_rewards, ep_lengths = [], []
        ep_r, ep_len = 0.0, 0

        for _ in range(self.cfg.rollout_len):
            action, log_prob, value = self.select_action(obs)
            next_obs, reward, done, _ = env.step(action)
            self.buffer.add(obs, action, log_prob, reward, value, float(done))
            ep_r += reward
            ep_len += 1
            obs = next_obs
            if done:
                ep_rewards.append(ep_r)
                ep_lengths.append(ep_len)
                ep_r, ep_len = 0.0, 0
                obs = env.reset()

        last_val = self.critic.forward(obs)
        self._last_value = last_val
        advantages, returns = self.buffer.compute_gae(
            last_val, self.cfg.gamma, self.cfg.gae_lambda
        )
        return {
            "mean_ep_reward": float(np.mean(ep_rewards)) if ep_rewards else 0.0,
            "mean_ep_length": float(np.mean(ep_lengths)) if ep_lengths else 0.0,
            "n_episodes": len(ep_rewards),
            "advantages_mean": float(advantages.mean()),
            "returns_mean": float(returns.mean()),
        }

    def update(self, advantages: np.ndarray,
               returns: np.ndarray) -> dict:
        """Optimize the clipped Gaussian-policy surrogate with CPU autograd.

        Existing NumPy inference weights remain the public representation.
        Gradient steps update all actor/critic layers and log standard deviation.
        This small implementation uses SGD, not an implicit Adam implementation.
        No policy usefulness or robot generalization follows from update passage.
        """
        import torch

        count = len(self.buffer.obs)
        if count == 0 or len(advantages) != count or len(returns) != count:
            raise ValueError("PPO update requires aligned nonempty rollout, advantages and returns")
        if self.cfg.batch_size <= 0 or self.cfg.n_epochs <= 0:
            raise ValueError("PPO batch size and epochs must be positive")
        obs = torch.tensor(np.asarray(self.buffer.obs), dtype=torch.float64)
        actions = torch.tensor(np.asarray(self.buffer.actions), dtype=torch.float64)
        old_log = torch.tensor(self.buffer.log_probs, dtype=torch.float64)
        target = torch.tensor(returns, dtype=torch.float64)
        adv = torch.tensor(advantages, dtype=torch.float64)
        if not all(torch.isfinite(v).all() for v in (obs, actions, old_log, target, adv)):
            raise ValueError("PPO inputs must be finite")
        adv = (adv - adv.mean()) / (adv.std(unbiased=False) + 1e-8)

        def parameters(network):
            return [torch.tensor(v.copy(), dtype=torch.float64, requires_grad=True)
                    for layer in (network.l1, network.l2, network.out) for v in (layer.W, layer.b)]

        actor = parameters(self.actor)
        log_std = torch.tensor(self.actor.log_std.copy(), dtype=torch.float64, requires_grad=True)
        actor.append(log_std)
        critic = parameters(self.critic)
        actor_optimizer = torch.optim.SGD(actor, lr=self.cfg.lr_actor)
        critic_optimizer = torch.optim.SGD(critic, lr=self.cfg.lr_critic)

        def forward(x, params, actor_output):
            x = torch.tanh(x @ params[0] + params[1])
            x = torch.tanh(x @ params[2] + params[3])
            x = x @ params[4] + params[5]
            return torch.tanh(x) if actor_output else x.squeeze(-1)

        logs = []
        for _ in range(self.cfg.n_epochs):
            order = self._rng.permutation(count)
            for start in range(0, count, self.cfg.batch_size):
                indices = order[start:start + self.cfg.batch_size]
                distribution = torch.distributions.Normal(
                    forward(obs[indices], actor, True), log_std.clamp(-20, 2).exp()
                )
                log_prob = distribution.log_prob(actions[indices]).sum(-1)
                ratio = (log_prob - old_log[indices]).exp()
                surrogate = torch.minimum(
                    ratio * adv[indices], ratio.clamp(1 - self.cfg.clip_eps, 1 + self.cfg.clip_eps) * adv[indices]
                )
                policy_loss = -surrogate.mean()
                value_loss = ((forward(obs[indices], critic, False) - target[indices]) ** 2).mean()
                entropy = distribution.entropy().sum(-1).mean()
                total_loss = policy_loss + self.cfg.value_coef * value_loss - self.cfg.entropy_coef * entropy
                if not torch.isfinite(total_loss):
                    raise ValueError("Nonfinite PPO loss; weights were not published")
                actor_optimizer.zero_grad()
                critic_optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(actor + critic, self.cfg.max_grad_norm, error_if_nonfinite=True)
                actor_optimizer.step()
                critic_optimizer.step()
                with torch.no_grad():
                    log_std.clamp_(-20, 2)
                logs.append([float(v.detach()) for v in (policy_loss, value_loss, entropy, total_loss)])

        for network, params in ((self.actor, actor), (self.critic, critic)):
            for index, layer in enumerate((network.l1, network.l2, network.out)):
                layer.W = params[2 * index].detach().numpy().copy()
                layer.b = params[2 * index + 1].detach().numpy().copy()
        self.actor.log_std = log_std.detach().numpy().copy()
        return dict(zip(("policy_loss", "value_loss", "entropy", "total_loss"), np.mean(logs, axis=0).tolist()))

    def train(self, env: NavEnv, n_updates: int = 50) -> list[dict]:
        """Main training loop."""
        for update in range(n_updates):
            stats = self.collect_rollout(env)
            advantages, returns = self.buffer.compute_gae(
                self._last_value, self.cfg.gamma, self.cfg.gae_lambda
            )
            loss_stats = self.update(advantages, returns)
            record = {"update": update + 1, **stats, **loss_stats}
            self.training_log.append(record)
            if (update + 1) % 10 == 0:
                logger.info(
                    "Update %3d | ep_r=%.2f | ep_len=%.1f | v_loss=%.4f",
                    update + 1, stats["mean_ep_reward"],
                    stats["mean_ep_length"], loss_stats["value_loss"]
                )
        return self.training_log
