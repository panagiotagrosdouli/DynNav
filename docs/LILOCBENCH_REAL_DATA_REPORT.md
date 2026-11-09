# LILocBench real-data robotics validation report

**Status:** reproducible public-data validation completed for map ingestion, map/ground-truth alignment, static A*, and offline ROS1 bag inspection. No live ROS graph, Nav2 playback, closed-loop navigation, or physical robot run was performed.

## Data and provenance

Downloaded from the official [LILocBench dataset page](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/) on 2026-11-09:

| Artifact | Source | Bytes | SHA-256 |
|---|---|---:|---|
| Occupancy-map archive | [`map_office.zip`](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/map_office.zip) | 17,415 | `941f96bf90d7d89dddf76fb4864f45212318d39f2b4f1220318786e53f48f6b0` |
| Extracted map metadata | `map_office.yaml` inside the archive | 130 | `6e61ed85520c2e4638684734c738daf63c17de830a535cd8458cee14cd1fb11e` |
| Extracted occupancy image | `map_office.png` inside the archive | 19,473 | `8a9ff6aa0d954e7743ed7dd1801d9df2a44a4d023cfda8de6ef12daa39cd57bf` |
| Ground-truth trajectory | [`dynamics_0/gt_poses.txt`](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/gt_poses_public/dynamics_0/gt_poses.txt) | 518,851 | `606f9392c1a992c9acdb5e680a9108ef7647ba8943d747435c90dfa56feaa38f` |
| Reduced ROS1 bag, without cameras | [`dynamics_0.bag`](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/bagfiles_no_cams/dynamics_0.bag) | 38,063,988 | `df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58` |

LILocBench describes `dynamics_0` as an indoor Clearpath Dingo sequence with moving people. The ground truth is provided for `base_link` in a global frame common across sequences. The occupancy map was made from the mapping sequence's front 2D LiDAR using ground-truth poses and scan-matching refinement. The map YAML is ROS1 map-server format. Dataset material is CC BY-NC-SA 4.0; attribution and per-file licensing are recorded in [`results/real_data/LICENSE.md`](../results/real_data/LICENSE.md).

Raw map, pose, and bag downloads are excluded from Git. Their checksums and analysis outputs are retained in [`lilocbench_map_and_trajectory_provenance.json`](../results/real_data/lilocbench_map_and_trajectory_provenance.json) and [`lilocbench_dynamics_0_ros1_bag_audit.json`](../results/real_data/lilocbench_dynamics_0_ros1_bag_audit.json).

## ROS map ingestion and static A* run

`scripts/inspect_ros_map.py` ingested the downloaded YAML and PNG with the existing `dynnav.mapping.ros_map.load_ros_map` path. It applied `negate: 0`, `occupied_thresh: 0.65`, `free_thresh: 0.196`, the ROS image-axis convention, and the declared unknown-as-blocked policy.

| Map property | Measured value |
|---|---:|
| Geometry | 1000 × 1000 cells |
| Resolution | 0.05 m/cell |
| YAML origin `[x, y, yaw]` | `[-25.0, -25.0, 0.0]` |
| Occupied or unknown cells blocked | 894,999 |
| Known-free cells | 105,001 |

The static route uses the first and last `dynamics_0` ground-truth samples as endpoints. They are valid known-free cells `(507, 359)` and `(651, 425)` at `(0.359727, -7.046163)` m and `(7.585787, -3.722195)` m in the dataset global frame.

| Static A* result | Value |
|---|---:|
| Reachable | Yes |
| Four-neighbour path | 225 cells / 224 steps |
| Path length | 11.20 m |
| Nodes expanded | 6,891 |
| Single local run time | 10.88 ms |

The observed ground-truth trajectory is 53.967 m long between those same first/last samples because it follows a recorded mission trajectory through the environment. The 11.20 m A* path is a static-map shortest-path baseline; comparing these lengths does not establish planner improvement or inefficiency.

Reproduce after downloading and extracting the official map, pose file, and reduced bag:

```bash
python -m pip install -e '.[dev,lilocbench]'
python scripts/inspect_ros_map.py /path/to/map_office.yaml \
  --start 0.3597271332,-7.0461629059 \
  --goal 7.5857874124,-3.7221946614
python scripts/generate_lilocbench_overlay.py \
  /path/to/map_office.yaml /path/to/gt_poses.txt \
  website/public/lilocbench-dynamics-0-verified-overlay.svg \
  --map-archive /path/to/map_office.zip \
  --path-csv results/real_data/lilocbench_dynamics_0_static_astar_path.csv
python scripts/analyze_lilocbench_ros1_bag.py /path/to/dynamics_0.bag \
  --ground-truth /path/to/gt_poses.txt \
  --output results/real_data/lilocbench_dynamics_0_ros1_bag_audit.json \
  --artifact-dir results/real_data
```

## Map-to-ground-truth frame alignment

The overlay uses the dataset's documented common global frame directly: no extra map-to-trajectory transform was fitted. The ROS map conversion applies the YAML origin and resolution, with yaw zero for this map. Empirical consistency checks found:

- All 3,194 ground-truth base positions are inside the map and land on cells classified known-free under the declared trinary thresholds.
- Repeating the point-in-cell check with the image's vertical axis left unflipped yields 0/3,194 known-free cells.
- The distance from each sampled base-position cell center to the nearest blocked cell center has minimum 0.224 m and median 0.949 m. This is a grid-center distance, not robot-footprint clearance or a safety margin.

The combination of source frame documentation, the provided map origin, and these occupancy checks supports the displayed map/ground-truth overlay. It is not an independent survey-control or point-cloud registration. It does not establish localization accuracy. The overlay is [`lilocbench-dynamics-0-verified-overlay.svg`](../website/public/lilocbench-dynamics-0-verified-overlay.svg); it visibly identifies the dataset, metrics, evidence status, source hashes, and license.

## ROS1 bag inspection and synchronization

The reduced bag is ROS1, not ROS2. The offline analyzer used the `rosbags` Python package to deserialize each recorded message in bag-time order; all 30,577 messages decoded. No ROS master, ROS2 node, TF listener, topic publisher, or real-time playback was started.

| Topic | Type | Messages |
|---|---|---:|
| `/dingo_velocity_controller/cmd_vel` | `geometry_msgs/Twist` | 6,866 |
| `/dingo_velocity_controller/odom` | `nav_msgs/Odometry` | 2,328 |
| `/joint_states` | `sensor_msgs/JointState` | 2,329 |
| `/laser_scan_front/scan` | `sensor_msgs/LaserScan` | 2,400 |
| `/laser_scan_rear/scan` | `sensor_msgs/LaserScan` | 2,400 |
| `/tf` | `tf/tfMessage`, `tf2_msgs/TFMessage` | 14,250 |
| `/tf_static` | `tf2_msgs/TFMessage` | 4 |

The bag spans 159.978 s. Odometry and joint-state header stamps are typically within 0.4 ms of bag record time; front and rear scan headers are typically within 0.15 ms and 0.12 ms, respectively. Nearest front/rear scan header skew has median 7.09 ms, 95th percentile 7.98 ms, and maximum 8.37 ms. Odom samples have median nearest-ground-truth time difference 12.50 ms; 99.83% are within 25 ms, with a maximum of 42.70 ms. These are timestamp comparisons, not a claim that all sensor messages are causally synchronized or consumed by a navigation stack.

The TF graph has a single root `odom`, includes `odom -> base_link` and scanner transforms, and has no `map`/`world` frame or `map -> odom` transform. The bag odometry therefore cannot be overlaid directly on the occupancy map. A diagnostic rigid XY fit from odometry to ground truth, fitted on the first 70% of paired times, has 0.145 m training RMSE but 0.408 m held-out RMSE on the last 30% (held-out 95th-percentile error 0.573 m). That fit is not a dataset-provided TF, is not used in the overlay, and is not suitable as a fixed map alignment.

The available bag supports offline inspection of recorded odometry, TF, velocity commands, wheel states, and LiDAR timestamps/ranges. It does not include a DynNav action-trigger event, map-update observation, paired counterfactual route, or recorded DynNav planner output.

## Evidence classification and limits

| Evidence type | Demonstrated here | Not demonstrated |
|---|---|---|
| Static map planning | Real map ingestion and A* reachability/route between valid data-derived endpoints | Dynamic replanning, risk reduction, recovery probability, or safety |
| Ground-truth replay | Recorded trajectory mapped to the official occupancy grid; bag headers/TF/odom/scan timing audited offline | Live ROS or Nav2 replay; command-to-motion response |
| Counterfactual simulation | Nothing in this report | What another planner would have done on the same recorded people/events |
| Closed-loop execution | Nothing in this report | Robot movement controlled by DynNav, Gazebo, or physical-robot trials |

LILocBench `dynamics_0` contains moving people, but the published sequence is not an action-triggered closure experiment. The static A* path is computed on the map made from a separate mapping run, not on a continuously updated map of each person. Do not claim that this validates the core dynamic-navigation efficacy hypothesis. The next scientifically valid step is a separate, controlled replay/simulation that defines how dynamic scans become time-indexed occupancy changes and then compares frozen planners on matched events; a physical causal claim still requires the preregistered robot study.
