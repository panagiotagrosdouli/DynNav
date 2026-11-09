import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from formal_safety_shields import CBFConfig, CBFSafetyFilter


class CBFProjectionTests(unittest.TestCase):
    def test_projection_satisfies_single_static_obstacle_constraint(self):
        filt = CBFSafetyFilter(CBFConfig(safety_radius=1.0, alpha=1.0))
        command, info = filt.batch_filter(
            np.array([-1.0, 0.0]), np.array([0.5, 0.0]), [np.array([0.0, 0.0])]
        )
        self.assertGreaterEqual(info["min_cbf_residual"], -1e-8)
        self.assertTrue(info["cbf_constraints_satisfied"])
        self.assertGreater(command[0], 0.0)

    def test_infeasible_opposing_constraints_are_reported(self):
        filt = CBFSafetyFilter(CBFConfig(safety_radius=1.0, alpha=1.0, max_iter=100))
        _, info = filt.batch_filter(
            np.zeros(2), np.zeros(2), [np.array([-0.5, 0.0]), np.array([0.5, 0.0])]
        )
        self.assertFalse(info["cbf_constraints_satisfied"])

    def test_rejects_invalid_config_and_nonfinite_commands(self):
        with self.assertRaises(ValueError):
            CBFConfig(alpha=0.0)
        filt = CBFSafetyFilter()
        with self.assertRaises(ValueError):
            filt.filter(np.array([np.nan, 0.0]), np.zeros(2), [])


if __name__ == "__main__":
    unittest.main()
