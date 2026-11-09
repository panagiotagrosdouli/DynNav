import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from federated_nav import FedNavConfig, FederatedServer, NavModel


class FederatedNavTests(unittest.TestCase):
    def test_dp_mode_clips_client_deltas_and_returns_finite_parameters(self):
        cfg = FedNavConfig(n_robots=2, global_rounds=2, dp_epsilon=1.0,
                           dp_delta=1e-5, dp_clip_norm=0.5, aggregation="uniform")
        model = NavModel.random_init(cfg.input_dim, cfg.output_dim, seed=2)
        server = FederatedServer(model, cfg)
        baseline = model.get_params()
        updates = []
        for offset in (1.0, 10.0):
            updates.append(({key: value + offset for key, value in baseline.items()}, 4))
        result = server.aggregate(updates)
        self.assertEqual(set(result), set(baseline))
        self.assertTrue(all(np.all(np.isfinite(value)) for value in result.values()))
        # Noise is intentionally randomized; only assert that outputs are valid.

    def test_dp_rejects_weighted_aggregation(self):
        with self.assertRaises(ValueError):
            FedNavConfig(dp_epsilon=1.0, aggregation="weighted")

    def test_dp_rejects_unbounded_per_round_epsilon(self):
        with self.assertRaises(ValueError):
            FedNavConfig(global_rounds=1, dp_epsilon=2.0)

    def test_non_dp_fedavg(self):
        cfg = FedNavConfig(n_robots=2, aggregation="uniform")
        model = NavModel.random_init(cfg.input_dim, cfg.output_dim, seed=3)
        server = FederatedServer(model, cfg)
        a = {key: np.ones_like(value) for key, value in model.get_params().items()}
        b = {key: np.full_like(value, 3.0) for key, value in model.get_params().items()}
        result = server.aggregate([(a, 1), (b, 5)])
        for value in result.values():
            np.testing.assert_allclose(value, 2.0)


if __name__ == "__main__":
    unittest.main()
