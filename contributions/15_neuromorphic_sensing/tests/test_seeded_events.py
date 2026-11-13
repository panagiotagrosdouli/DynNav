"""Repeatability covers timestamp jitter even when background noise is zero."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

path = Path(__file__).resolve().parents[1] / "neuromorphic_sensing.py"
spec = importlib.util.spec_from_file_location("c15_seeded_events", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


@pytest.mark.parametrize("noise", [0.0, 0.2])
def test_same_seed_reproduces_signal_noise_and_timestamps(noise):
    cfg = module.DVSSimulatorConfig(height=4, width=4, noise_rate=noise, seed=7)
    a, b = module.DVSSimulator(cfg), module.DVSSimulator(cfg)
    for intensity in [0.1, 0.9, 0.1]:
        frame = np.full((4, 4), intensity)
        assert a.process_frame(frame) == b.process_frame(frame)


def test_seed_controls_jitter_even_without_noise():
    a = module.DVSSimulator(module.DVSSimulatorConfig(height=2, width=2, noise_rate=0, seed=1))
    b = module.DVSSimulator(module.DVSSimulatorConfig(height=2, width=2, noise_rate=0, seed=2))
    for sensor in (a, b):
        assert sensor.process_frame(np.full((2, 2), 0.1)) == []
    x, y = a.process_frame(np.ones((2, 2))), b.process_frame(np.ones((2, 2)))
    assert len(x) == len(y) == 4
    assert x != y


@pytest.mark.parametrize("dt", [0, -1, float("nan")])
def test_invalid_time_intervals_are_rejected(dt):
    sensor = module.DVSSimulator(module.DVSSimulatorConfig(height=2, width=2))
    with pytest.raises(ValueError):
        sensor.process_frame(np.ones((2, 2)), dt_us=dt)
