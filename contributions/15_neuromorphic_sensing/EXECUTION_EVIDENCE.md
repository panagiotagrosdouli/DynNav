# C15 — reproducible experiment and claim boundaries

**Evidence:** The registered `c15_neuromorphic_latency` synthetic benchmark **executed successfully** in [run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This is real software execution, not hardware or scientific generalization evidence.

## Hypothesis

Event-stream obstacle detection can reduce detection latency for moving targets while maintaining low false-negative rates relative to frame sampling.

## Exact command and original source

```bash
python scripts/run_contribution_suite.py --only C15 --fail-on-skip --output-dir results/contribution_audit/C15
```

Entry point: `contributions/15_neuromorphic_sensing/experiments/eval_neuromorphic_latency.py`.

Independent per-contribution outputs include `manifest.json`, `summary.md`, a nonempty CSV and SHA-256; the [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) and its artifact `c02-c26-per-file-and-per-contribution-execution` preserve all 25 reports. The file-level auditor additionally inspects each source script, binary model, data file, plot and document in this contribution.

## Baselines and metrics

- **Baselines:** [Frame-based detector].
- **Primary metrics:** [detected, detection_time_us, latency_us, false_negative, event_rate_per_ms].
- **Evidence level:** synthetic.
- **Specific research limitation:** Simulated events and Python timing do not establish hardware event-camera latency.

## Not established

A successful controlled runner does not prove trained-model performance, held-out site generalization, robust actual sensor inputs, real ROS 2 integration, robot-controller safety, formal mathematical proof, or real physical-robot navigation. These are separate experiments requiring actual available data/hardware and appropriate baselines, authenticated provenance and independent review. **Verified physical C15 trials: 0.**
