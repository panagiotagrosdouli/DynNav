import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nerf_uncertainty import NeRFConfig, TinyNeRF


class TinyNeRFProxyTests(unittest.TestCase):
    def test_mc_dropout_is_reproducible_for_equal_seeds(self):
        points = np.ones((4, 3))
        dirs = np.ones((4, 3))
        a = TinyNeRF(NeRFConfig(seed=17))
        b = TinyNeRF(NeRFConfig(seed=17))
        np.testing.assert_array_equal(a.query(points, dirs, training=True)[1],
                                      b.query(points, dirs, training=True)[1])

    def test_rejects_invalid_config_and_query_shapes(self):
        with self.assertRaises(ValueError):
            TinyNeRF(NeRFConfig(n_uncertainty_samples=0))
        model = TinyNeRF(NeRFConfig())
        with self.assertRaisesRegex(ValueError, "matching shape"):
            model.query(np.zeros((2, 3)), np.zeros((1, 3)))


if __name__ == "__main__":
    unittest.main()
