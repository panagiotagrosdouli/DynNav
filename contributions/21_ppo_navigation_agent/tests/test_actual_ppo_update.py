"""PPO must change parameters using real gradients, including truncated GAE."""

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("torch")
path = Path(__file__).resolve().parents[1] / "ppo_nav_agent.py"
spec = importlib.util.spec_from_file_location("c21_actual_ppo", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_policy_learns_directional_bandit_signal_and_critic_updates():
    cfg = module.PPOConfig(
        obs_dim=2, action_dim=1, hidden_dim=8, lr_actor=0.05, lr_critic=0.05, n_epochs=4, batch_size=64
    )
    agent = module.PPOAgent(cfg)
    obs = np.array([0.4, -0.2])
    before = agent.actor.forward(obs)[0].item()
    critic_before = agent.critic.out.W.copy()
    for _ in range(5):
        agent.buffer.clear()
        actions = []
        for _ in range(64):
            action, log_prob, value = agent.select_action(obs)
            actions.append(action.item())
            agent.buffer.add(obs, action, log_prob, action.item(), value, 1.0)
        result = agent.update(np.asarray(actions), np.asarray(actions))
        assert all(np.isfinite(v) for v in result.values())
    assert agent.actor.forward(obs)[0].item() > before + 0.1
    assert not np.array_equal(critic_before, agent.critic.out.W)


def test_gae_bootstraps_truncation_but_not_terminal_episode():
    buffer = module.RolloutBuffer()
    buffer.add(np.zeros(2), np.zeros(1), 0, 1, 0.5, 0.0)
    advantage, _ = buffer.compute_gae(2.0, 0.9, 0.95)
    assert advantage[0] == pytest.approx(2.3)
    buffer.dones[0] = 1.0
    advantage, _ = buffer.compute_gae(2.0, 0.9, 0.95)
    assert advantage[0] == pytest.approx(0.5)


def test_rollouts_are_reproducible_from_seed():
    cfg = module.PPOConfig(obs_dim=13)
    a, b = module.NavEnv(cfg, seed=13), module.NavEnv(cfg, seed=13)
    np.testing.assert_array_equal(a.reset(), b.reset())
    for _ in range(5):
        x, r, done, _ = a.step(np.array([0.1, 0.2]))
        y, s, other, _ = b.step(np.array([0.1, 0.2]))
        np.testing.assert_array_equal(x, y)
        assert (r, done) == (s, other)
