# C01 — Real recorded sensor data and ROS 2 Jazzy execution report

**Date:** 2026-11-09  
**Primary scope:** Evidence that official physical-world Dingo sensor data can
be decoded, converted to rosbag2 and received by ROS 2 Jazzy subscriber nodes.
This is **not** evidence of C01-controlled physical robot motion.

## Verified source and acquisition

Official source:
https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/

Source robotic platform: Clearpath Dingo (actual instrumented robot);
source recording `dynamics_0`, approximately 10 moving people near the robot.

Original no-camera ROS 1 bag URL:
https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/bagfiles_no_cams/dynamics_0.bag

Official file length: **38,063,988 bytes**.  
Original file SHA-256:
`df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58`.

Dataset attribution: N. Trekel et al., *Benchmark for Evaluating Long-Term
Localization in Indoor Environments Under Substantial Static and Dynamic
Scene Changes*, IROS 2025. License: CC BY-NC-SA 4.0. The CI does not upload
or redistribute the raw or converted bag; it uploads only provenance and
measurements.

## Successful genuine recorded-message decoding

[GitHub Actions run #42687499291](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42687499291)
successfully downloaded the original physical Dingo ROS bag and decoded the
original serialized messages with the `rosbags` library.

The audit `experiments/inspect_recorded_rosbag.py` extracted **25,920
messages** from the selected relevant topics:

| Original topic | Recorded message type | Actual decoded messages |
|---|---|---:|
| `/laser_scan_front/scan` | `sensor_msgs/msg/LaserScan` | 2,400 |
| `/laser_scan_rear/scan` | `sensor_msgs/msg/LaserScan` | 2,400 |
| `/dingo_velocity_controller/odom` | `nav_msgs/msg/Odometry` | 2,328 |
| `/dingo_velocity_controller/cmd_vel` | `geometry_msgs/msg/Twist` | 6,866 |
| `/tf` | `tf2_msgs/msg/TFMessage` | 11,922 |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | 4 |
| **Total** | | **25,920** |

The recorded sequence spans approximately 160 seconds. The counts were
observed by actual bag decoding, not invented from documentation or inferred
solely from a metadata file.

## Successful ROS 2 Jazzy converted-bag playback

[GitHub Actions run #42687940440](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42687940440)
successfully:

1. Downloaded the genuine official ROS 1 bag again.
2. Converted it to rosbag2 using `rosbags-convert`.
3. Ran actual `ros2 bag info` on the converted ROS 2 bag (30,577 total
   messages in the converted bag, including topics not selected by the
   focused offline decoder; not a contradictory message count).
4. Ran actual ROS 2 Jazzy `ros2 bag play`.
5. Received at least five live ROS 2 subscriptions each on the front/rear
   LaserScan, odometry and TF topics. Subscriber
   `experiments/ros2_verify_recorded_replay.py` retained the nonzero counts
   and explicitly set `physical_robot_control_verified=false`.

This is **real recorded hardware data replayed through functioning ROS 2
middleware**. A successful replay does not establish that C01 was the planner
originally used to command the Dingo or that its outputs are closed-loop
validated.

## Actual C01 algorithm evaluation on real map geometry

[Official LILocBench occupancy-map run #42681341639](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42681341639)
ran the saved C01 neural model on five paired generated, reachable map queries.
The saved model was genuinely loaded. Original map (1000×1000, 0.05m/cell)
and model SHA-256 were retained in [REAL_DATA_PROTOCOL.md](REAL_DATA_PROTOCOL.md).

| Method | Mean expansions | Mean measured search runtime |
|---|---:|---:|
| Manhattan A* | 12,648.8 | 59.19 ms |
| Learned raw | 14,740.8 | 975.74 ms |
| Learned clipped | 15,082.2 | 1,010.29 ms |

The pilot found a **negative** learned-search efficiency outcome on its five
real-map queries. The source robot did not execute those generated paths.

## ROS 2 C01 planner interface evaluation

- `experiments/ros2_get_plan_node.py`: actual C01 Manhattan/learned search
  algorithms exposed as `nav_msgs/srv/GetPlan` with a no-fallback checkpoint
  requirement and output route validation; **planning-only**.
- `experiments/ros2_get_plan_roundtrip_test.py`: actual ROS 2 message
  transport integration test using a labelled synthetic occupancy-grid fixture
  and a real `GetPlan` service call.
- `.github/workflows/c01-real-rosbag.yml`: dedicated CI running recorded
  sensor decoding, ROS 1-to-ROS 2 conversion/playback, and ROS 2 GetPlan
  roundtrip. Its **latest** GetPlan step must be inspected before marking
  that particular integration as verified.

ROS 2 GetPlan roundtrip and ROS 2 recorded bag playback are distinct tests:
the roundtrip fixture does **not** assert that the recorded Dingo trajectory
was produced by C01 or that the C01 service consumed its LiDAR data.

## Evidence hierarchy and unresolved work

| Evidence | Status |
|---|---|
| Official physical robot map geometry + offline C01 planning | Verified |
| Authentic physical robot ROS 1 LiDAR/odom recording decoded | Verified |
| Authentic recorded sensor messages replayed as ROS 2 Jazzy messages | Verified |
| C01 actual ROS 2 GetPlan service roundtrip | CI execution status to verify |
| C01 real-time obstacle handling under closed-loop ROS 2 Nav2 | NOT VERIFIED |
| Real physical robot movement controlled by C01 | **0 verified trials** |
| Properly paired C01-vs-baseline hardware navigation outcomes | **0 verified trials** |

Physical experiments require a named connected robot, a reviewed Nav2
planner/controller bridge, actual operator hardware-safety checks and
authentic synchronized robot telemetry. None can be manufactured from
archived bag replay.

## Reproduction

The complete reproducible recorded-data job is
`.github/workflows/c01-real-rosbag.yml`. For local ROS 1 decoding:

```bash
python -m pip install rosbags
python contributions/01_learned_astar/experiments/inspect_recorded_rosbag.py \
  /path/to/dynamics_0.bag \
  --output /tmp/c01_dingo_recorded_audit.json
```

For ROS 1-to-ROS 2 conversion, from the actual sourced Jazzy environment:

```bash
rosbags-convert --src /path/to/dynamics_0.bag --dst /tmp/c01_ros2_dingo
ros2 bag info /tmp/c01_ros2_dingo
```

The replay observer is a read-only subscriber. Do not play old robot
`cmd_vel` into an active physical robot controller or a shared ROS domain
without safe remapping/isolation; the CI uses an isolated container.
