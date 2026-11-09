import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from risk_budget import RiskBudgetTracker


class RiskBudgetTests(unittest.TestCase):
    def test_tracks_overspend_without_accepting_negative_risk(self):
        tracker = RiskBudgetTracker(0.5)
        tracker.consume(0.7)
        self.assertAlmostEqual(tracker.remaining(), -0.2)
        self.assertTrue(tracker.will_violate(0.0))
        with self.assertRaises(ValueError):
            tracker.consume(-0.1)

    def test_rejects_invalid_budget_and_prediction(self):
        with self.assertRaises(ValueError):
            RiskBudgetTracker(float("nan"))
        with self.assertRaises(ValueError):
            RiskBudgetTracker(1.0).will_violate(float("inf"))


if __name__ == "__main__":
    unittest.main()
