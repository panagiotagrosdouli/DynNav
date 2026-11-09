import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ppo_nav_agent import NavEnv, PPOAgent, PPOConfig


class PPOTrainingScopeTests(unittest.TestCase):
    def test_train_does_not_claim_learning_without_optimizer(self):
        cfg = PPOConfig(obs_dim=14, hidden_dim=8, rollout_len=4)
        agent = PPOAgent(cfg)
        before = agent.actor.out.W.copy()
        with self.assertRaises(NotImplementedError):
            agent.train(NavEnv(cfg), n_updates=1)
        self.assertTrue((agent.actor.out.W == before).all())


if __name__ == "__main__":
    unittest.main()
