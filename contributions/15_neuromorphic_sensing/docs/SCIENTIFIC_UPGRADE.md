# C15 Scientific Upgrade Notes — Neuromorphic Latency Benchmark

## What was already strong

Contribution 15 already introduced a strong bio-inspired sensing idea:

> Use event-camera style asynchronous sensing and a lightweight spiking detector for low-latency obstacle response.

The existing module includes:

- a DVS/event-camera simulator,
- ON/OFF events based on log-intensity changes,
- refractory period handling,
- event time surfaces,
- leaky integrate-and-fire neurons,
- an SNN-style obstacle detector.

This is useful because high-speed obstacles may be detected earlier through event streams than through standard frame-based perception.

## Main weakness before this upgrade

The original module described low latency, but did not measure it directly.

A reviewer could ask:

> Does the event-based detector actually react earlier than a frame-based baseline?

or:

> How many events are generated, and does the detector miss fast motion?

## New contribution added

C15 now includes:

```text
neuromorphic_benchmark.py
experiments/eval_neuromorphic_latency.py
```

The new benchmark evaluates:

- detection latency,
- false-negative status,
- number of generated events,
- event rate per millisecond,
- maximum detection score,
- comparison against a frame-based baseline.

## New benchmark

Run:

```bash
python contributions/15_neuromorphic_sensing/experiments/eval_neuromorphic_latency.py
```

Output:

```text
contributions/15_neuromorphic_sensing/results/c15_neuromorphic_latency.csv
```

The benchmark compares slow, medium, and fast synthetic moving obstacles.

## Reviewer-safe claim

A stronger claim after this upgrade is:

> Contribution 15 evaluates event-camera obstacle detection using explicit latency and false-negative metrics against a frame-based baseline on moving-obstacle sequences.

## Relationship to other contributions

C15 connects directly to:

- C03 risk-aware planning when event detections increase local obstacle risk,
- C05 safe mode when fast obstacle evidence appears,
- C08 IDS when sensor event statistics become abnormal,
- C12 diffusion occupancy when event streams update future occupancy risk.

## Limitations

- The benchmark uses synthetic greyscale moving obstacles.
- The SNN detector is lightweight and randomly initialized, not trained.
- The frame baseline is simple and intended for auditability, not a production vision model.
- Real event-camera validation requires DVS hardware logs and timestamp-accurate control measurements.

## Next research step

The strongest extension is event-triggered safe-mode activation:

```text
event burst -> obstacle probability -> local risk spike -> safe-mode slowdown
```

This would connect C15 directly to C05 and make low-latency sensing actionable for navigation.
