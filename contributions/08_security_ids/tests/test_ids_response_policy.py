import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from ids_response_policy import IDSResponseConfig, classify_ids_response, PlannerMitigation


class IDSResponsePolicyTests(unittest.TestCase):
    def test_thresholds_and_evidence_validation(self):
        with self.assertRaises(ValueError):
            IDSResponseConfig(watch_ratio=2, warning_ratio=1)
        with self.assertRaises(ValueError):
            classify_ids_response({"d2": 1.0, "thr": 0.0})
        with self.assertRaises(ValueError):
            classify_ids_response({"flag_rate": 1.5})
        with self.assertRaises(ValueError):
            classify_ids_response({"triggered": "false"})

    def test_critical_evidence_requests_stop(self):
        result = classify_ids_response({"d2": 3.0, "thr": 1.0, "flag_rate": 0.0,
                                        "triggered": False, "streak": 0})
        self.assertEqual(result.mitigation, PlannerMitigation.EMERGENCY_STOP)


if __name__ == "__main__":
    unittest.main()
