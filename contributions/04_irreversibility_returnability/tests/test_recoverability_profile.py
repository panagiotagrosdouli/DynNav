"""Tests for route-level recoverability profiles."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

MODULE_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = MODULE_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from recoverability_metrics import build_path_recoverability_profile  # noqa: E402


class RecoverabilityProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = np.zeros((9, 9), dtype=np.int32)
        self.grid[0, :] = 1
        self.grid[-1, :] = 1
        self.grid[:, 0] = 1
        self.grid[:, -1] = 1
        self.base = (1, 4)

    def test_single_state_route_has_zero_degradation(self) -> None:
        profile = build_path_recoverability_profile(
            self.grid,
            [self.base],
            self.base,
        )

        self.assertEqual(profile.path_len, 1)
        self.assertEqual(profile.cumulative_recoverability_loss, 0.0)
        self.assertEqual(profile.maximum_single_step_loss, 0.0)
        self.assertTrue(profile.all_returnable)

    def test_commitment_away_from_base_creates_recoverability_loss(self) -> None:
        route = [(1, 4), (2, 4), (3, 4), (4, 4), (5, 4)]
        profile = build_path_recoverability_profile(self.grid, route, self.base)

        self.assertGreater(profile.cumulative_recoverability_loss, 0.0)
        self.assertGreater(profile.maximum_single_step_loss, 0.0)
        self.assertLess(profile.terminal_recoverability, profile.mean_recoverability)

    def test_repeated_fragile_commitments_are_not_hidden_by_endpoint(self) -> None:
        direct = [(1, 4), (2, 4), (3, 4)]
        oscillating = [(1, 4), (2, 4), (3, 4), (2, 4), (3, 4)]

        direct_profile = build_path_recoverability_profile(self.grid, direct, self.base)
        oscillating_profile = build_path_recoverability_profile(
            self.grid,
            oscillating,
            self.base,
        )

        self.assertAlmostEqual(
            direct_profile.terminal_recoverability,
            oscillating_profile.terminal_recoverability,
        )
        self.assertGreater(
            oscillating_profile.cumulative_recoverability_loss,
            direct_profile.cumulative_recoverability_loss,
        )

    def test_penalty_rejects_negative_weights(self) -> None:
        profile = build_path_recoverability_profile(
            self.grid,
            [(1, 4), (2, 4)],
            self.base,
        )

        with self.assertRaises(ValueError):
            profile.penalty(minimum_weight=-1.0)


if __name__ == "__main__":
    unittest.main()
