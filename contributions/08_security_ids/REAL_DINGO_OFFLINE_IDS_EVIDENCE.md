# C08 — Genuine recorded Dingo odometry and offline synthetic IDS challenge

**Verified workflow:** [C08 actual Dingo recorded odometry with injected counterfactual #42781562230](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42781562230) completed successfully. At that head the 4 focused original attack-audit tests passed, and the authentic source bag SHA-256 was verified: `df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58`.

## Actual measured results — important unfavorable result

The physical Clearpath Dingo's already-recorded `/dingo_velocity_controller/odom` was decoded **offline**; C08 had not controlled the Dingo during the recording. A speed-offset anomaly was artificially added **in memory**, never to the original bag or a live robot.

| Quantity | Observed / experimental value |
|---|---:|
| Actual recorded odometry messages decoded | **2,328** |
| Valid consecutive velocity observations | **2,327** |
| Earlier training-only baseline samples | **1,047** |
| Later held-out samples | **1,280** |
| Synthetic injected speed offset (not a real attack) | **+0.35 m/s** |
| Held-out unmodified alarm-positive samples | **0** |
| Artificially injected case, pre-injection alarm-positive samples | **0** |
| Detected an alarm after artificial injection? | **Yes** |
| **Detection delay** | **521 samples** |
| Calibrated CUSUM threshold | **1,996.0475**, normalized-score units |

### Scientific interpretation

**A delay of 521 samples is a very weak timely-detection result.** It cannot be presented as effective prompt intrusion detection or safety. Moreover the original recording has no independent attack labels or assured clean baseline. Zero observed alarms on the unmodified segment is *not* a measured false-positive rate against annotated attack-free ground truth. The huge threshold was conservatively estimated from an earlier sample period, while the underlying vehicle velocity profile is nonstationary. The CUSUM statistic here is **a normalized speed-deviation heuristic**, not state-estimator innovation NIS. There is no evidence of any real compromised sensor.

This experiment is useful as a candid initial baseline and demonstrates technical ability to process authentic odometry and synthesize a controlled counterfactual. It does **not** validate real attack detectability, low latency, calibrated FPR, state-estimator integrity, ROS2 live cyber mitigation or real physical robot safety.

## Actual code and test paths

- `experiments/eval_real_dingo_odometry_synthetic_attack.py`: source bag decoding, finite chronological motion filtering, time-separated baseline fit and held-out evaluation, independent raw vs artificially modified reporting, immutable input hash.
- `tests/test_real_dingo_offline_attack.py`: malformed odometry, replay invariants, synthetic-only labeling.
- `code/security_monitor_cusum.py`: repair broken import of the actual `utils.sequential_ids` module from arbitrary working directories.
- `tests/test_security_monitor_import.py`: run the real legacy NIS/EWMA/CUSUM adapter, including deliberate alarm and reset.
- `.github/workflows/c08-recorded-dingo-ids.yml`: actual original ROS1 bag download + SHA-256 verification, execution, tests and JSON artifact.

## Reproducibility

```bash
python contributions/08_security_ids/experiments/eval_real_dingo_odometry_synthetic_attack.py \
  /path/to/official_LILocBench_dynamics_0.bag \
  --output results/c08_recorded_dingo/ids_report.json \
  --attack-speed .35
```

The CI artifact `c08-original-dingo-odometry-offline-injected-ids` retains the JSON report, not a redistributed Dingo bag.

## Remaining publication and safety gates

Require independent time-synchronized localization/TF/estimator innovation ground truth, known attack labels, multiple traces and sites, predeclared severity/latency targets, holdout-calibrated false-alarm statistics, benign-domain-shift negative controls and live ROS2 IDS/mitigation tested **without compromising an uncontrolled robot**. For physical hardware safety, an onsite operator, independently testable stop system and authenticated source ROS2 recording remain prerequisites.

**Physical C08 robot trials verified here: 0. Cyberattack incidents actually observed here: 0.**
