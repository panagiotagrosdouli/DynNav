import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adversarial_attacks import AttackConfig, GradientAttacker, LiDARAttacker


class AttackReproducibilityTests(unittest.TestCase):
    def test_pgd_is_seeded_and_respects_linf_budget(self):
        x = np.full(5, 0.5)
        cfg = AttackConfig(seed=9, epsilon=0.1, pgd_steps=3)
        loss = lambda value: float(np.sum((value - 0.9) ** 2))
        a = GradientAttacker(cfg).pgd(x, loss)
        b = GradientAttacker(cfg).pgd(x, loss)
        np.testing.assert_array_equal(a, b)
        self.assertLessEqual(float(np.max(np.abs(a - x))), cfg.epsilon + 1e-12)

    def test_lidar_attacks_are_seeded_and_config_is_validated(self):
        cfg = AttackConfig(seed=4, lidar_n_phantoms=2)
        cloud = np.zeros((3, 3))
        a = LiDARAttacker(cfg).spoof_add(cloud, np.zeros(3))
        b = LiDARAttacker(cfg).spoof_add(cloud, np.zeros(3))
        np.testing.assert_array_equal(a, b)
        with self.assertRaisesRegex(ValueError, "epsilon"):
            AttackConfig(epsilon=-0.1)


if __name__ == "__main__":
    unittest.main()
