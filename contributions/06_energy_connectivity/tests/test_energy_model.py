import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from energy_model import EnergyModel, EnergyParams


class EnergyModelTests(unittest.TestCase):
    def test_cost_is_nonnegative_and_risk_dependent(self):
        model = EnergyModel(EnergyParams(move_cost=2.0, risk_energy_coeff=3.0))
        self.assertAlmostEqual(model.step_energy_cost(0.5), 3.5)
        with self.assertRaises(ValueError):
            model.step_energy_cost(-0.1)

    def test_rejects_negative_or_nonfinite_energy_parameters(self):
        with self.assertRaisesRegex(ValueError, "move_cost"):
            EnergyParams(move_cost=-1.0)
        with self.assertRaisesRegex(ValueError, "e0"):
            EnergyParams(e0=float("inf"))


if __name__ == "__main__":
    unittest.main()
