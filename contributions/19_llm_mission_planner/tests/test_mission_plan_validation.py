import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm_mission_planner import LLMMissionPlanner, LLMPlannerConfig


class MissionPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.planner = LLMMissionPlanner(LLMPlannerConfig(known_zones=["kitchen", "start"]))

    def test_valid_plan_parsed_and_prioritized(self):
        mission = self.planner._parse_llm_response("go", '{"confidence":0.9,"waypoints":[{"label":"start","priority":2},{"label":"kitchen","priority":1}]}')
        self.assertEqual([waypoint.label for waypoint in mission.waypoints], ["kitchen", "start"])

    def test_unknown_zones_invalid_actions_and_duplicate_priorities_rejected(self):
        cases = [
            '{"confidence":0.9,"waypoints":[{"label":"secret_room","priority":1}]}',
            '{"confidence":0.9,"waypoints":[{"label":"kitchen","priority":1,"action":"launch"}]}',
            '{"confidence":0.9,"waypoints":[{"label":"kitchen","priority":1},{"label":"start","priority":1}]}',
            '{"confidence":NaN,"waypoints":[]}',
        ]
        for raw in cases:
            with self.subTest(raw=raw):
                self.assertIsNone(self.planner._parse_llm_response("go", raw))

    def test_empty_instruction_rejected_without_query(self):
        with self.assertRaises(ValueError):
            self.planner.parse("  ")


if __name__ == "__main__":
    unittest.main()
