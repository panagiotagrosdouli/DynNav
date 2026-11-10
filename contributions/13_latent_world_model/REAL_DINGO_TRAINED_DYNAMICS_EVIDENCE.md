# C13 — Trained action-conditioned dynamics on original Dingo hardware recordings

**Experiment date:** 2026-11-10  
**Verified dedicated CI:** [Run #42791098890](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42791098890), successfully executed real ROS1 bag download, SHA-256 verification, tests, model training, and disjoint chronological test evaluation.

## Data provenance and actual physical observations

Original source: LILocBench genuine Clearpath Dingo indoor recording `dynamics_0.bag`, original SHA-256 `df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58`. Acquired by the LILocBench team, not C13.

| Dataset element | Count |
|---|---:|
| Actual recorded Dingo odometry messages | 2,328 |
| Actual recorded `cmd_vel` Twist messages | 6,866 |
| Valid chronological aligned odometry/action steps | 2,305 |
| Held-out chronological test windows | 453 |

Recorded past control commands are aligned only at times **at or before** the initial odometry timestamp for each predicted step, rejecting potential future-command leakage. Motion labels are transformed to the robot's previous body frame. Irregular gaps, implausible jumps, missing commands and invalid values are excluded under predeclared thresholds. This is *actual physically recorded motion and action-conditioned supervision*; no new robot command was sent.

Data are split into time-ordered **65% training, 15% validation, 20% final test**, with a full history-window gap between blocks to avoid reusing training histories in the test. Normalization uses training-only statistics. Model checkpoint retains source identity, split boundaries, parameter tensors and all normalization statistics.

## Actual model and training

The new implementation is a **PyTorch GRU(6→24) plus a 3-output action-conditioned transition head**. The input consists of eight prior body-motion/command/time-step observations and the next historical action and duration (all commands causally available at the preceding observation time). Targets are one-step body-frame forward/lateral displacement and change in yaw.

This is a trained **one-step transition model**. It is not the older NumPy `RSSM`, a complete action-conditioned DreamerV3, a trained stochastic posterior with uncertainty coverage, or a demonstrated long-horizon imagined planner.

Training completed for 8 epochs. Validation normalized MSE improved from **0.187941** to **0.114029** at the best saved epoch; checkpoint selection used validation only, not final test metrics.

## Actual measured held-out test errors

| Algorithm | Translation RMSE | Rotation RMSE |
|---|---:|---:|
| Commanded kinematic | 0.00120505 m | 0.00504702 rad |
| Last-step persistence | **0.00073104 m** | 0.00289486 rad |
| Zero-motion | 0.02656904 m | 0.01314570 rad |
| Trained GRU | 0.00093700 m | **0.00175001 rad** |

**Mixed scientific result:** the trained GRU improves yaw prediction relative to all three baselines, but is **worse than simple last-step persistence** in translational RMSE. It beats the command-only kinematic translation baseline, but cannot be claimed globally superior. These results are from one original recording, one chronological split and one seed; no confidence interval, robot-to-robot generalization or deployment robustness is established.

## Reproduction

```bash
python contributions/13_latent_world_model/experiments/train_real_dingo_action_dynamics.py \
  /path/to/original/dynamics_0.bag \
  --output-dir results/c13_actual_dingo \
  --epochs 8 --history 8 --seed 2026
```

The [dedicated C13 GitHub Actions workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c13-real-dingo-dynamics.yml) actually installs CPU PyTorch and `rosbags`, confirms official recording hash/byte size, trains and validates, and uploads `c13_trained_real_dingo_dynamics.pt` plus `report.json`, **not the original raw recording**.

Regression tests verify causal alignment, body-frame transforms, group/window separation and training-only normalization. The existing `experiments/eval_rollout_audit.py` remains a separate **synthetic untrained RSSM** evaluation and must not be credited to these actual trained weights.

## Remaining requirements for the research claim

Real multi-session training and held-out robot/scene evaluation, multi-step trajectory rollout validity and cumulative-error curves, explicit predictive uncertainty calibration and posterior/prior training, action-dependent risk/collision ground-truth labels, multiple random seeds and recovery/irreversibility comparisons, and actual ROS 2 integration with reviewed controller safety are still absent.

**Physical C13-controlled Dingo navigation trials verified: zero.** The Dingo was physically moving in the historical source recording, but C13 did not command that motion.
