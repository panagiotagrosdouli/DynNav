import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from risk_map_evaluator import evaluate_risk_map
from diffusion_occupancy import DiffusionOccupancyConfig, DiffusionOccupancyPredictor, ScoreNetwork
from diffusion_occupancy import DiffusionOccupancyConfig, DiffusionOccupancyPredictor, ScoreNetwork


class RiskMapValidationTests(unittest.TestCase):
    def test_metrics_accept_valid_probability_and_soft_target_maps(self):
        metrics = evaluate_risk_map(np.array([[0.2, 0.8]]), np.array([[0.0, 1.0]]))
        self.assertAlmostEqual(metrics.brier_score, 0.04)
        self.assertAlmostEqual(metrics.accuracy_at_05, 1.0)

    def test_invalid_probabilities_targets_cvar_and_threshold_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_risk_map(np.array([[1.2]]), np.array([[1.0]]))
        with self.assertRaises(ValueError):
            evaluate_risk_map(np.array([[0.2]]), np.array([[np.nan]]))
        with self.assertRaises(ValueError):
            evaluate_risk_map(np.array([[0.2]]), np.array([[0.0]]), cvar_map=np.array([[2.0]]))
        with self.assertRaises(ValueError):
            evaluate_risk_map(np.array([[0.2]]), np.array([[0.0]]), high_risk_threshold=1.1)

    def test_prediction_is_seeded_and_conditioned(self):
        cfg = DiffusionOccupancyConfig(grid_h=3, grid_w=3, T=2, n_samples=2, history_len=1)
        a = DiffusionOccupancyPredictor(cfg).predict_risk([np.zeros((3, 3))])
        b = DiffusionOccupancyPredictor(cfg).predict_risk([np.zeros((3, 3))])
        np.testing.assert_array_equal(a["mean"], b["mean"])
        net = ScoreNetwork(3, 3, seed=1)
        x = np.zeros((3, 3))
        score_empty = net.forward(x, 1, x)
        score_full = net.forward(x, 1, np.ones((3, 3)))
        self.assertFalse(np.allclose(score_empty, score_full))

    def test_invalid_history_and_path_rejected(self):
        predictor = DiffusionOccupancyPredictor(
            DiffusionOccupancyConfig(grid_h=2, grid_w=2, T=2, n_samples=1, history_len=1)
        )
        with self.assertRaises(ValueError):
            predictor.predict_risk([np.full((2, 2), 2.0)])
        with self.assertRaises(ValueError):
            predictor.risk_weighted_cost([(5, 5)], {"cvar_95": np.zeros((2, 2))})

    def test_prediction_is_seeded_and_conditioned(self):
        cfg = DiffusionOccupancyConfig(grid_h=3, grid_w=3, T=2, n_samples=2, history_len=1)
        a = DiffusionOccupancyPredictor(cfg).predict_risk([np.zeros((3, 3))])
        b = DiffusionOccupancyPredictor(cfg).predict_risk([np.zeros((3, 3))])
        np.testing.assert_array_equal(a["mean"], b["mean"])
        net = ScoreNetwork(3, 3, seed=1)
        x = np.zeros((3, 3))
        score_empty = net.forward(x, 1, x)
        score_full = net.forward(x, 1, np.ones((3, 3)))
        self.assertFalse(np.allclose(score_empty, score_full))

    def test_invalid_history_and_path_rejected(self):
        predictor = DiffusionOccupancyPredictor(
            DiffusionOccupancyConfig(grid_h=2, grid_w=2, T=2, n_samples=1, history_len=1)
        )
        with self.assertRaises(ValueError):
            predictor.predict_risk([np.full((2, 2), 2.0)])
        with self.assertRaises(ValueError):
            predictor.risk_weighted_cost([(5, 5)], {"cvar_95": np.zeros((2, 2))})


if __name__ == "__main__":
    unittest.main()
