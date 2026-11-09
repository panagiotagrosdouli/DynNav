import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from swarm_consensus import BFTConsensus, NavProposal
from swarm_consensus_evaluator import path_is_valid


def proposal(robot_id, cost, confidence=1.0, path=None):
    return NavProposal(robot_id, path or [(0, 0), (0, 1)], cost, confidence)


class CentralizedSelectorTests(unittest.TestCase):
    def test_outlier_does_not_win_by_claiming_high_confidence(self):
        selector = BFTConsensus(3, min_participants=1.0)
        result = selector.reach_consensus([
            proposal(0, 2.0, confidence=0.2),
            proposal(1, 2.1, confidence=0.3),
            proposal(2, 999.0, confidence=1.0),
        ])
        self.assertEqual(result.method, "centralized_mad_median")
        self.assertEqual(result.rounds, 1)
        self.assertEqual(result.agreed_path, [(0, 0), (0, 1)])
        self.assertEqual(result.n_byzantine_detected, 1)

    def test_insufficient_quorum_abstains(self):
        selector = BFTConsensus(3, min_participants=0.67)
        result = selector.reach_consensus([proposal(0, 1.0)])
        self.assertEqual(result.agreed_path, [])
        self.assertEqual(result.method, "abstain_insufficient_participants")

    def test_duplicate_and_invalid_proposals_rejected(self):
        selector = BFTConsensus(2)
        with self.assertRaises(ValueError):
            selector.reach_consensus([proposal(0, 1), proposal(0, 2)])
        with self.assertRaises(ValueError):
            selector.reach_consensus([proposal(0, float("nan"))])

    def test_evaluator_rejects_corrupted_path(self):
        import numpy as np
        grid = np.zeros((3, 3))
        self.assertTrue(path_is_valid(grid, [(0, 0), (0, 1), (1, 1)], (0, 0), (1, 1)))
        self.assertFalse(path_is_valid(grid, [(0, 0), (2, 2), (1, 1)], (0, 0), (1, 1)))


if __name__ == "__main__":
    unittest.main()
