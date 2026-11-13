# C08 — Actual recorded-Dingo odometry IDS and counterfactual bias study

## Scientific provenance

[Passing Dingo source experiment #42781562230](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42781562230) downloaded and SHA-256 verified an original LILocBench physical Clearpath Dingo ROS1 bag, decoded authentic odometry and ran a CUSUM implementation on chronological derived speed measurements. The source bag digest is `df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58`.

**Authentic observations, original bag:** 2,328 odometry observations yielded **2,327 valid speed samples**. An early **1,047-sample** segment set the CUSUM configuration. The independent later **1,280-sample** period was held out.

**Artificial attack:** a +0.35 m/s bias was added **only in a Python array**, starting halfway through held-out data. This was not a real attack, not a manipulated ROS2 TF stream, and not a physical vehicle experiment.

## Measured result at +0.35 m/s

| Variable | Measured result |
|---|---:|
| Source physical odometry observations | 2,328 |
| Valid speed increments | 2,327 |
| Baseline fitting samples | 1,047 |
| Held-out test samples | 1,280 |
| Positive injected speed perturbation | +0.35 m/s (synthetic) |
| Alarms on unmodified held-out original stream | 0 |
| Artificial perturbation detected after onset | Yes |
| Delay to detected post-onset alarm | **521 samples** |
| Configured CUSUM threshold | 1996.0475 |

**Interpretation:** This is detection under a particular counterfactual perturbation, but **521 samples is a long delay** and the result must not be described as a rapid/safety-ready IDS. There are no independent cyber-attack labels for the original recording: a zero-alarm count is not a measured true-negative rate.

### Sensitivity comparison

[Successful run #42782628901](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42782628901) **executed** five explicitly synthetic in-memory biases on the same original recorded Dingo stream, with the same chronological baseline configuration and independently reported results:

| Injected artificial speed bias | Post-onset detected? | Delay in samples |
|---|---|---:|
| +0.10 m/s | No | Not detected |
| +0.20 m/s | No | Not detected |
| +0.35 m/s | Yes | 521 |
| +0.50 m/s | Yes | 367 |
| +1.00 m/s | Yes | 176 |

The result indicates a **weak IDS that misses both lower-level perturbations and reacts slowly to stronger ones**. These are **sample-count delays**, not seconds, and are not physically observed attacks. The same original unlabelled historical data were used for all tests; this does not establish external detection rates. Reproducible evidence is saved in `sensitivity/sensitivity.csv` and `sensitivity/summary.json`, included in the dedicated workflow artifact.

## Reproduction

```bash
python contributions/08_security_ids/experiments/eval_real_dingo_odometry_synthetic_attack.py \
  /path/to/dynamics_0.bag \
  --attack-speed 0.35 \
  --output results/c08_recorded_dingo/ids_report.json

python contributions/08_security_ids/experiments/eval_dingo_injection_sensitivity.py \
  /path/to/dynamics_0.bag \
  --output-dir results/c08_recorded_dingo/sensitivity \
  --biases 0.1 0.2 0.35 0.5 1.0
```

See [C08 recorded Dingo CI workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c08-recorded-dingo-ids.yml). The original source bag is downloaded independently and is **not redistributed** in artifacts.

## Evidence categories and unresolved work

This analysis contains genuine **historical physical-world odometry**, a real Python IDS inference experiment, and **offline artificial counterfactual injection**. No physical or real cyberattack took place and no actuating commands were emitted. It does NOT prove an IDS is installed onboard the Dingo, deployed as a real-time ROS2 trust monitor, properly calibrated under operator-induced attacks, robust to sensor covariance shift, or able to prevent unsafe robot motion.

**Verified C08 physical onboard trials: 0.** Actual physical robot validation requires the specific connected platform, authenticated sensor/estimator innovation feeds, synchronized ROS2 events, separate baseline/attack sessions, strict safety operator and an independent emergency-stop mechanism.
