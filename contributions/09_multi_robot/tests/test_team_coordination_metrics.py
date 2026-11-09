import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from team_coordination_metrics import RobotPlan, detect_path_conflicts, summarize_team_coordination


class TeamCoordinationMetricTests(unittest.TestCase):
    def test_detects_vertex_and_edge_swap_conflicts(self):
        a = RobotPlan("a", [(0, 0), (0, 1), (0, 2)], 0.1, 0.2)
        b = RobotPlan("b", [(0, 1), (0, 0), (0, 2)], 0.1, 0.2)
        events = detect_path_conflicts([a, b])
        self.assertEqual({event.conflict_type for event in events}, {"vertex", "edge_swap"})

    def test_duplicate_ids_and_invalid_risk_rejected(self):
        a = RobotPlan("a", [(0, 0)], 0.1, 0.2)
        with self.assertRaises(ValueError):
            summarize_team_coordination([a, a])
        with self.assertRaises(ValueError):
            RobotPlan("bad", [(0, 0)], float("nan"), 0.2)


if __name__ == "__main__":
    unittest.main()
