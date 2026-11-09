import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from neuromorphic_sensing import DVSEvent, DVSSimulator, DVSSimulatorConfig, event_to_time_surface


class NeuromorphicInputTests(unittest.TestCase):
    def test_simulation_reproduces_seeded_event_stream(self):
        cfg = DVSSimulatorConfig(height=4, width=4, noise_rate=0.1, seed=9)
        frame = np.zeros((4, 4))
        frame[1:3, 1:3] = 1.0
        events_a = DVSSimulator(cfg).process_frame(frame)
        events_b = DVSSimulator(cfg).process_frame(frame)
        self.assertEqual(events_a, events_b)

    def test_rejects_invalid_frames_and_events(self):
        sim = DVSSimulator(DVSSimulatorConfig(height=2, width=2))
        with self.assertRaises(ValueError):
            sim.process_frame(np.full((2, 2), np.nan))
        with self.assertRaises(ValueError):
            event_to_time_surface([DVSEvent(3, 0, 0.0, 1)], 2, 2)


if __name__ == "__main__":
    unittest.main()
