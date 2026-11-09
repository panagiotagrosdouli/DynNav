import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from multimodal_failure_explainer import FailureReport
from failure_report_evaluator import FailureExplanationExpectation, score_failure_report


class FailureReportEvaluatorTests(unittest.TestCase):
    def test_scores_valid_report(self):
        report = FailureReport("collision", 1.0, (0.0, 0.0), "obstacle", [("path_risk", 0.4)],
                               "robustness -0.1", ["reduce speed", "increase radius"], 0.8)
        scored = score_failure_report(report, FailureExplanationExpectation(
            "case", ("path_risk",), ("speed",), True
        ))
        self.assertEqual(scored.root_cause_recall, 1.0)
        self.assertGreaterEqual(scored.total_score, 0.0)

    def test_invalid_confidence_and_nonfinite_cause_rejected(self):
        report = FailureReport("collision", 1.0, (0.0, 0.0), "scene", [("cause", float("nan"))],
                               "summary", ["action"], 1.1)
        with self.assertRaises(ValueError):
            score_failure_report(report, FailureExplanationExpectation("case", (), ()))


if __name__ == "__main__":
    unittest.main()
