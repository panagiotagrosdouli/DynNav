import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from uncertainty_calibrator import GlobalScaleCalibrator, coverage


class UncertaintyCalibrationTests(unittest.TestCase):
    def test_rejects_negative_uncertainty_scale(self):
        with self.assertRaisesRegex(ValueError, "sigma"):
            coverage([0.1], [-0.2], 1.0)

    def test_rejects_invalid_coverage_multiplier_and_absolute_error(self):
        with self.assertRaisesRegex(ValueError, "multiplier"):
            coverage([0.1], [0.2], float("nan"))
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            GlobalScaleCalibrator().fit([-0.1], [0.2])


if __name__ == "__main__":
    unittest.main()
