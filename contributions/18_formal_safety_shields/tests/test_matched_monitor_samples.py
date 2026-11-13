"""Shield comparisons require one monitor observation per physical step."""
import importlib.util
from pathlib import Path
import sys

import numpy as np

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("c18_matched_monitor", root / "shield_evaluator.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_shield_and_baseline_monitor_identical_number_of_steps(monkeypatch):
    monitors = []
    original = module.STLMonitor

    class CountingMonitor(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.samples = 0
            monitors.append(self)

        def update(self, state):
            self.samples += 1
            return super().update(state)

    monkeypatch.setattr(module, "STLMonitor", CountingMonitor)
    for shielded in (False, True):
        result = module.rollout_to_goal(
            scenario="matched_monitor", shielded=shielded,
            start=np.array([0., 0.]), goal=np.array([2., 0.]),
            obstacles=[np.array([4., 4.])], steps=7,
        )
        assert result.steps == 7
    assert [monitor.samples for monitor in monitors] == [7, 7]
