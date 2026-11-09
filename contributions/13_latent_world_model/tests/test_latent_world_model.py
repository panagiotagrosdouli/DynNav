import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from latent_world_model import RSSMConfig, WorldModelPlanner


class WorldModelBoundaryTests(unittest.TestCase):
    def test_seeded_random_sequences_reproduce(self):
        cfg = RSSMConfig(obs_dim=4, action_dim=2, latent_dim=3, hidden_dim=5, seed=17)
        a = WorldModelPlanner(config=cfg).generate_random_sequences(2, horizon=3)
        b = WorldModelPlanner(config=cfg).generate_random_sequences(2, horizon=3)
        for seq_a, seq_b in zip(a, b):
            for action_a, action_b in zip(seq_a, seq_b):
                np.testing.assert_array_equal(action_a, action_b)

    def test_invalid_observations_and_empty_candidates_rejected(self):
        planner = WorldModelPlanner(config=RSSMConfig(obs_dim=4, action_dim=2,
                                                       latent_dim=3, hidden_dim=5))
        with self.assertRaises(ValueError):
            planner.update_belief(np.zeros(3), np.zeros(2))
        with self.assertRaises(ValueError):
            planner.select_best_action_sequence([])
        with self.assertRaises(ValueError):
            planner.generate_random_sequences(0)


if __name__ == "__main__":
    unittest.main()
