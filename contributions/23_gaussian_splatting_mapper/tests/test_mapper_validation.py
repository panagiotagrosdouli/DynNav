import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gaussian_splatting_map import GSMapConfig, GaussianSplattingMap


class GaussianMapValidationTests(unittest.TestCase):
    def test_merge_covariance_uses_preupdate_mean(self):
        mapper = GaussianSplattingMap(GSMapConfig(merge_threshold=2.0))
        mapper.add_frame(np.zeros((1, 3)))
        mapper.add_frame(np.asarray([[0.1, 0.0, 0.0]]))
        self.assertAlmostEqual(mapper.gaussians[0].cov[0, 0], 0.01)

    def test_rejects_mismatched_colors_and_invalid_pose(self):
        mapper = GaussianSplattingMap()
        with self.assertRaisesRegex(ValueError, "colors"):
            mapper.add_frame(np.zeros((2, 3)), colors=np.zeros((1, 3)))
        with self.assertRaisesRegex(ValueError, "pose"):
            mapper.add_frame(np.zeros((1, 3)), pose=np.eye(3))


if __name__ == "__main__":
    unittest.main()
