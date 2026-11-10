# C15 — Time-aligned simulated event sensing versus frame baseline

**Date:** 2026-11-10. **Verified CI:** [C15 execution #42793602006](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42793602006), **passed** with 4 focused tests and independently checked 12 method runs (6 paired scenarios).

## Why the original comparison was not scientifically fair

The historical `eval_neuromorphic_latency.py` passed `dt_us=10000` (10 ms) to the DVS simulator while the frame baseline used `dt_us=33333` (33.333 ms). Those different input schedules confound sensor sampling with algorithmic detection latency. Furthermore, the DVS simulator reconstructs events **from complete greyscale frames**, so it does not provide genuine high-rate, asynchronous DVS timestamps and cannot be compared to a lower-rate frame camera to establish a physical event sensing advantage.

The new `experiments/eval_time_aligned_latency.py` passes the **same generated sequence of frames and the same timestamp interval** to both pipelines for 3 obstacle speeds × 2 frame periods.

## Actual measured CI outcomes

| Obstacle speeds | Input periods | Paired test cases | Frame threshold detected | Random SNN-style event detector detected |
|---|---|---:|---:|---:|
| 3, 6, 10 px/frame | 10 ms, 33.333 ms | 6 | **6/6** | **0/6** |

The frame method sees the bright obstacle in the **first source frame** (reported index-time 0 μs). The event detector in the current implementation never crosses its configured threshold in these six paired trials. **No event-minus-frame latency should be calculated for trials where the event method failed to detect**; `null` is used instead of a fabricated time. The event input contains *synthetically generated* pixel events but the detector's random SNN-style weights have not been trained to recognize obstacles.

This negative outcome is not proof that real event cameras are slower or worse than frame sensors. It disproves a claimed speed advantage for **this specific existing randomly initialized model on these frames**, with sampling-rate bias removed.

## Verification and reproduction

```bash
python -m pytest -q contributions/15_neuromorphic_sensing/tests
python contributions/15_neuromorphic_sensing/experiments/eval_time_aligned_latency.py \
  --output-dir results/c15_fair_latency
```

The dedicated `.github/workflows/c15-fair-dvs-latency.yml` additionally executes the original historical benchmark for contrast. The CI artifact `c15-fair-event-vs-frame-synthetic-timing` contains `paired_trials.csv`, `summary.json` and `legacy_cadence_confounded.csv`. Source and result identifiers are explicit so the two studies cannot be conflated.

## Scientific evidence still missing

- An actual event-camera dataset such as a validly licensed DSEC/MVSEC recording with event timestamps and independently annotated obstacles.
- Proper event-based and frame-based detectors trained/validated with disjoint sequences and **synchronized acquisition clocks**.
- Equal compute/time/energy budgets and separate latency accounting for sensor capture, transport, batching and inference.
- Real ROS2 event message subscriptions and integration with C05 safe mode.
- New actual physical trials with measured event sensor input, synchronized motion/safety logs and a safety operator.

**Verified physical C15 robot-controlled trials: 0. The code processes synthetic frame-derived events, not actual Dingo event-camera recordings.**
