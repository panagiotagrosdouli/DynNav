import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from nbv_scoring import NBVWeights, ViewCandidate, score_candidates


class NBVScoringTests(unittest.TestCase):
    def test_returnability_changes_selection_when_information_is_equal(self):
        candidates = [
            ViewCandidate("long_returnable", 2.0, 2.0, 0.1, 1.0, 1.0),
            ViewCandidate("short_trapped", 2.0, 1.0, 0.1, 0.0, 0.2),
        ]
        rows = score_candidates(candidates)
        self.assertEqual([r.name for r in rows if r.selected_by_classic], ["short_trapped"])
        self.assertEqual([r.name for r in rows if r.selected_by_safe], ["long_returnable"])

    def test_rejects_invalid_candidate_and_weights(self):
        with self.assertRaises(ValueError):
            ViewCandidate("bad", -1, 1, 0, 0, 0)
        with self.assertRaises(ValueError):
            ViewCandidate("nan", 1, float("nan"), 0, 0, 0)
        with self.assertRaises(ValueError):
            NBVWeights(risk_weight=-1)


if __name__ == "__main__":
    unittest.main()
