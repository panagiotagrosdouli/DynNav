import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from safe_mode_controller import SafeModeConfig, SafeModeController, SafeModeState


class SafeModeControllerTests(unittest.TestCase):
    def test_cooldown_blocks_full_number_of_updates(self):
        controller = SafeModeController(SafeModeConfig(
            activation_steps_required=1, recovery_steps_required=1, cooldown_steps=2
        ))
        self.assertEqual(controller.update(0.8).state, SafeModeState.SAFE_MODE)
        recovered = controller.update(0.2)
        self.assertEqual(recovered.state, SafeModeState.NORMAL)
        self.assertEqual(recovered.cooldown_remaining, 2)
        self.assertEqual(controller.update(0.8).state, SafeModeState.NORMAL)
        self.assertEqual(controller.update(0.8).state, SafeModeState.NORMAL)
        self.assertEqual(controller.update(0.8).state, SafeModeState.SAFE_MODE)

    def test_invalid_risk_and_config_rejected(self):
        controller = SafeModeController()
        for risk in (float("nan"), -0.1, 1.1):
            with self.subTest(risk=risk), self.assertRaises(ValueError):
                controller.update(risk)
        with self.assertRaises(ValueError):
            SafeModeConfig(risk_on_threshold=float("inf"))


if __name__ == "__main__":
    unittest.main()
