import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from language_safety_policy import LanguageSafetyConfig, LanguageSafetyPolicy


class LanguageSafetyPolicyTests(unittest.TestCase):
    def test_negative_safety_phrase_is_not_treated_as_neutral(self):
        decision = LanguageSafetyPolicy().evaluate("The corridor is not safe")
        self.assertGreater(decision.risk_scale, 1.0)
        self.assertIn("explicitly unsafe condition", decision.factors)

    def test_neutral_marker_requires_word_boundary_and_config_is_validated(self):
        policy = LanguageSafetyPolicy()
        self.assertEqual(policy.evaluate("normal").risk_scale, 1.0)
        self.assertGreater(policy.evaluate("abnormal crowd").risk_scale, 1.0)
        with self.assertRaises(ValueError):
            LanguageSafetyConfig(base_risk=2.0, max_risk_scale=1.0)
        with self.assertRaises(TypeError):
            policy.evaluate(None)


if __name__ == "__main__":
    unittest.main()
