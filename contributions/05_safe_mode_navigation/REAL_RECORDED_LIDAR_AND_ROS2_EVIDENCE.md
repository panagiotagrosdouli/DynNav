# C05 — Executed real recorded Dingo LiDAR study and real ROS 2 safe-mode supervision

**Date: 2026-11-09. Evidence classes: actual prerecorded physical robot measurements consumed OFFLINE; genuine ROS 2 Jazzy middleware on SYNTHETIC scalar inputs. They are different experiments. Neither establishes that C05 commanded a physical robot.**

## 1. Real Dingo LiDAR recording: actually executed

[Successful GitHub Actions run #42714751251](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42714751251) downloaded the original 38,063,988-byte LILocBench Dingo ROS 1 dynamics_0 bag (not a repackaged synthetic fixture) from the University of Bonn data service. Provenance:

- Official recording URL: https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/bagfiles_no_cams/dynamics_0.bag
- SHA-256: **df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58**
- Actual LiDAR source topic: /laser_scan_front/scan
- 4,800 real LaserScan messages examined; 480 evenly subsampled LiDAR scans actually decoded and evaluated.
- Observed recorded span: timestamps 1733314486.6165–1733314646.281773 (approx. 159.7 seconds, from the original bag).

The explicitly declared proximity **proxy**, not a probability of collision, was calculated as follows:

    q10 = 10th percentile of valid finite laser ranges within sensor min/max
    scalar_proxy = clip((2.0 meters - q10) / 1.5 meters, 0, 1)
    no valid range => critical risk 1.0

The original C05 hysteresis/controller state machine consumed those real recorded observations **offline**, updating once per selected scan. No original Dingo actions, odometry or navigation route were modified.

## 2. Actual offline policy results

| Computed outcome | C05 on real prerecorded LiDAR sequence |
|---|---:|
| Evaluated recorded scans | 480 |
| NORMAL states | 17 |
| SAFE_MODE states | 9 |
| EMERGENCY_STOP states | **454** |
| Mode transitions | 6 |
| Replanning flags | 4 |
| Operator alert states | 454 |
| Mean scalar proxy | 0.84432 |
| Mean commanded **policy speed scale** | 0.04198 |

The baseline policy is an illustrative constant nominal speed scale of 1.0; it does not represent a real robot drive or measured trajectory. The 454 emergency states should **not** be treated as 454 genuine emergencies, verified hazards, actual motor stops, avoided collisions, or physical hardware actions. This proxy is likely excessively conservative in a cluttered indoor map. The exploratory analysis is strong evidence that C05 *processes genuine LiDAR input*, and highlights the need to calibrate threshold/scaling from independent geometric obstacle ground truth and robot-specific clearance constraints.

One CSV row per evaluated real scan and all source provenance are retained in the workflow artifact **c05-genuine-dingo-lidar-offline-safe-mode-decisions**. Raw third-party bag content is never committed to Git.

## 3. Real ROS 2 Jazzy policy diagnostics and stale-feed watchdog

[Successful GitHub Actions run #42714751045](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42714751045) ran distinct genuine ROS2 publishers/subscribers with the actual C05 controller:

- **11 ROS2 Float64 synthetic risk observations delivered** in sequence; the intended normal, persistence-based safe-mode, critical-stop and recovery transitions were verified.
- A non-finite NaN risk sample caused the supervisory **EMERGENCY_STOP software state**, with output speed scale exactly zero.
- After the input feed stopped, the **real watchdog timer** produced an additional **12th diagnostic response** and maintained the safe emergency-stop state.
- All ROS2 diagnostics explicitly recorded zero physical-robot movement and no actuator publishing.

These are genuine ROS2 software messages but the risk values of this ROS2 experiment were generated; they were not physically measured LiDAR data and did not drive Nav2, Gazebo, the Dingo motors or a certified hardware E-stop.

## 4. Confirmed engineering flaw corrected

Previously SafeModeController.update accepted NaN, infinity and values outside [0,1] without input classification. Comparisons with NaN are false, potentially retaining NORMAL or incorrectly allowing release from emergency state. The policy now **fails closed**: invalid risks are replaced with a finite critical telemetry sentinel, force emergency-stop mode and zero speed-scale, and produce an explicit INVALID_RISK transition. Invalid non-finite/unsafe configuration thresholds, speeds and inflation radii are rejected.

Focused regression tests cover NaN/Inf, out-of-range, startup, persistence, cooldown and emergency recovery. Actual recorded LiDAR preprocessing regression tests validate invalid beams and conservative empty scan behavior.

## 5. Reproduction

    python contributions/05_safe_mode_navigation/experiments/eval_recorded_dingo_lidar_safe_mode.py /path/to/dynamics_0.bag --output-dir results/c05_real_dingo_lidar --max-scans 500 --stride 10

GitHub Actions workflows:

- .github/workflows/c05-real-recorded-dingo-lidar.yml
- .github/workflows/c05-ros2-safe-mode.yml

The ROS2 supervisor is in experiments/ros2_safe_mode_supervisor.py and live publisher/subscriber validation in experiments/ros2_safe_mode_roundtrip.py.

## 6. Scientific limits and next hardware gates

An actual robot-controlled claim requires independently commissioned C05 actuation enforcement, clear safety response to loss of messages, robot-specific velocity and braking constraints, physical distance sensors or surveyed obstacle ground truth, synchronized ROS2 bags showing that C05 truly affected physical motor commands, and an on-site trained operator with a physical E-stop. Static thresholds derived from this experiment alone are NOT a physical safety guarantee.

**Verified physical robot C05 trials: 0.**
