# Contribution 15 — Neuromorphic Sensing for Low-Latency Obstacle Detection

[![Module](https://img.shields.io/badge/Module-15-purple)](.) [![Type](https://img.shields.io/badge/Type-Neuromorphic%20%2F%20Bio--inspired-blue)](.) [![Status](https://img.shields.io/badge/Status-Core%20Upgraded-brightgreen)](.)

> **Critical corrected benchmarking evidence:** [TIME_ALIGNED_LATENCY_EVIDENCE.md](TIME_ALIGNED_LATENCY_EVIDENCE.md) reports the executed time-aligned six-scenario comparison. With equal frame input frequency, the existing randomly initialized SNN detected **0/6** obstacles while the frame baseline detected **6/6**. A neuromorphic latency advantage is **not demonstrated**. Both inputs were synthetic greyscale-derived events, not physical DVS sensor recordings.

## Plain-language summary

Frame cameras observe the world in fixed snapshots.

Event cameras observe changes as they happen.

Contribution 15 explores this idea for navigation. It simulates an event camera and uses a lightweight spiking neural network style detector to identify moving obstacles with low latency.

The upgraded version adds a latency benchmark, so the contribution can test the actual claim:

> Does event-based sensing react earlier than a simple frame-based pipeline?

---

## Research Question

> **RQ15:** Does event-camera-based obstacle detection reduce reaction latency and false negatives in high-speed scenarios compared with frame-based perception?

This contribution studies:

- Dynamic Vision Sensor simulation,
- asynchronous ON/OFF events,
- event time surfaces,
- leaky integrate-and-fire neurons,
- SNN-style obstacle detection,
- moving-obstacle latency,
- false-negative behaviour.

---

## Conceptual Pipeline

```text
greyscale frames
      ↓
DVS simulator
      ↓
asynchronous ON/OFF events
      ↓
time surface representation
      ↓
SNN obstacle detector
      ↓
obstacle probability grid
      ↓
safe-mode or planner update
```

---

## Existing Components

The original C15 implementation includes:

- `DVSSimulator`,
- `DVSSimulatorConfig`,
- `DVSEvent`,
- `event_to_time_surface`,
- `LIFNeuron`,
- `SNNObstacleDetector`.

These components provide a lightweight, dependency-free simulation of event-based obstacle perception.

---

## New Upgrade Added

C15 now includes:

```text
neuromorphic_benchmark.py
```

This module evaluates detection performance using:

- detection latency,
- false-negative status,
- number of events,
- event rate per millisecond,
- maximum detection score,
- comparison against a frame-based baseline.

---

## Files

```text
15_neuromorphic_sensing/
├── README.md
├── neuromorphic_sensing.py
├── neuromorphic_benchmark.py
├── docs/
│   └── SCIENTIFIC_UPGRADE.md
├── experiments/
│   └── eval_neuromorphic_latency.py
└── results/
    └── c15_neuromorphic_latency.csv
```

---

## Quick Start

Run the new latency benchmark:

```bash
python contributions/15_neuromorphic_sensing/experiments/eval_neuromorphic_latency.py
```

This generates:

```text
contributions/15_neuromorphic_sensing/results/c15_neuromorphic_latency.csv
```

---

## Benchmark Scenarios

The benchmark compares:

| Scenario | Meaning |
|---|---|
| `slow_obstacle` | Slowly moving bright obstacle |
| `medium_obstacle` | Medium-speed moving obstacle |
| `fast_obstacle` | Fast-moving obstacle |

For each scenario, it evaluates:

- event/SNN detection,
- simple frame-based detection.

---

## Metrics

| Metric | Meaning |
|---|---|
| Detection latency | Time until detector first reports obstacle |
| False negative | Whether the obstacle was missed |
| Number of events | Total generated DVS events |
| Event rate | Events per millisecond |
| Max score | Maximum detector confidence |

---

## Scientific Contribution

The upgraded C15 contribution is not simply:

> Simulate event-camera outputs.

It is stronger:

> Evaluate whether event-based obstacle detection provides lower-latency response than frame-based detection on moving-obstacle sequences.

This makes the neuromorphic sensing claim measurable.

---

## Integration

- **Feeds into:** C03 risk-aware planning as fast local obstacle risk
- **Triggers:** C05 safe mode when event bursts indicate imminent obstacle risk
- **Can be monitored by:** C08 IDS when event rates become abnormal
- **Can update:** C12 future occupancy risk maps
- **ROS 2 integration:** publish event stream on `/dvs/events`

Recommended runtime interface:

```text
neuromorphic_output = {
    events,
    event_rate,
    time_surface,
    obstacle_probability_grid,
    detection_latency
}
```

---

## Limitations

- The benchmark uses synthetic greyscale moving obstacles.
- The SNN detector is lightweight and randomly initialized.
- The frame baseline is intentionally simple and audit-friendly.
- Real validation requires DVS hardware or event-camera datasets.
- The current detector does not yet perform learned spiking classification.

---

## Next Research Step

The strongest extension is event-triggered safe-mode activation:

```text
event burst
      ↓
obstacle probability spike
      ↓
local risk increase
      ↓
safe-mode slowdown or emergency stop
```

This would connect C15 directly to C05 and make low-latency sensing actionable.

---

## Conclusion

Contribution 15 establishes the neuromorphic sensing layer of DynNav.

The upgraded version adds explicit latency evaluation, making the contribution stronger and more experimentally grounded.

### Reproducible simulator event timestamps

`DVSSimulatorConfig(seed=...)` now controls both background noise and within-frame
timestamp jitter through one persistent generator. Previously a new unseeded RNG
was constructed for every frame, so timestamps varied even with zero noise.
Finite input and positive finite frame intervals are required. Seeded replay is
an implementation property, not a demonstrated neuromorphic sensing advantage;
previous negative latency findings remain unchanged.

The revised synthetic benchmark/control use explicit event simulator seed `0`.
This is a declared reproducibility revision; historical unseeded measurements
are retained and are not relabeled as generated by the seeded implementation.
