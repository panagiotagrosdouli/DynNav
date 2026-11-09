# C01 — Executed ROS 2 closed-loop navigation evidence (2026-11-09)

## Verified implementation and CI execution

[GitHub Actions run 42695311932](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42695311932) **completed successfully** in a genuine ROS 2 Jazzy container. The job ran the actual C01 `ros2_get_plan_node.py` service in three modes and a separate `ros2_isolated_closed_loop.py` controller/kinematic-plant process using **real ROS 2 message transport**.

**Pipeline:** C01 `nav_msgs/srv/GetPlan` → returned planned poses → waypoint-following controller → ROS2 `geometry_msgs/msg/Twist` on `/c01/isolated_sim/cmd_vel` → deterministic simulated differential-drive plant → ROS2 `nav_msgs/msg/Odometry` on `/c01/isolated_sim/odom` → controller feedback → goal.

The synthetic 12×12 occupancy grid contains a blocking wall with a single gap. The simulated plant checks occupancy after each update and retains every simulated pose and command. All actuation-like topics are deliberately prefixed `/c01/isolated_sim/`, and the GitHub Actions job uses `ROS_DOMAIN_ID=155`. **No physical robot, real-world controller, Gazebo physics, or original Dingo movement was used in this closed-loop study.**

## Actual measured run (single trial per planner mode)

| C01 mode | Simulated goal reached | Simulated trajectory distance | Simulated duration | Final goal error | Occupancy collisions | ROS2 Twist received | ROS2 Odometry received |
|---|---|---:|---:|---:|---:|---:|---:|
| Manhattan A* | Yes | 4.31195 m | 13.2 s | 0.06726 m | 0 | 131 | 132 |
| Raw Learned A* | Yes | 4.24673 m | 14.4 s | 0.06758 m | 0 | 143 | 144 |
| Clipped Learned A* | Yes | 4.31195 m | 13.2 s | 0.06726 m | 0 | 131 | 132 |

Measured C01 service planning latency in the same run:

| Planner | One service-planning latency |
|---|---:|
| Manhattan A* | 0.610 ms |
| Raw Learned A* | 6.403 ms |
| Clipped Learned A* | 6.214 ms |

For learned modes the actual checkpoint SHA-256 was
`640ec68fcf1a04b3fc3abbc146ff5aaaee58a5a170ec5770c39459cce972b19a`.
A successful trial required both genuine `GetPlan` diagnostics for the chosen C01 planner and nonzero separately transported ROS2 Twist and Odometry messages. The independent CI acceptance step confirmed all three goal completions, zero cell collisions, final position within 0.12m of the goal, and the explicit non-hardware evidence label.

The result is a **positive software integration finding**, not a claim that raw neural A* is faster, safer or more robust in realistic environments. The three trajectories are from just one selected synthetic scenario; no uncertainty bands or physical success rate can be estimated from this sample. The simulator lacks wheel slip, latency/jitter modeling, realistic LiDAR perception, dynamic obstacles and physical control safety checks.

## Separation from authentic real-world data evidence

Previous C01 investigations actually executed:

- [LILocBench real occupancy map + saved neural checkpoint](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42681341639): five paired offline map queries with **negative mean learned-search efficiency result**.
- [Original physical-world Dingo ROS1 bag decoding](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42687499291): 25,920 genuinely recorded messages, including front/rear LiDAR and odometry.
- [Converted Dingo ROS bag playback via real ROS2 Jazzy subscriptions](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42687940440): ROS2 live subscriber reception of archived physical-world data.
- [C01 ROS2 GetPlan on official LILocBench occupancy geometry](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42690187837): one paired real-map query where raw learned expanded 209 nodes vs Manhattan 1,782, but took 13.35ms vs 10.03ms.

**These tests form complementary evidence categories, not one combined physical execution.** The historical Dingo was driven by the original data-acquisition team in December 2024. The available ROS1 bag does not establish C01 was installed onboard and cannot be rewritten to do so.

## What would make the physical-robot claim true?

1. Document a **new** physical robot trial with C01 selected as the active planner in a reviewed and tested ROS2/Nav2 controller integration.
2. An onsite operator must confirm a functional independent emergency stop, calibrated sensor/footprint and safe speed/clearance requirements.
3. Retain synchronized map, `/scan`, `/odom`, `/tf`, Nav2 goals/results, actual `/cmd_vel`, and C01 planner diagnostics and checkpoint identity.
4. Compare matched physical start/goal tasks against Manhattan A* in predeclared randomized order, preserve failures, and independently inspect ROS2 bags.
5. Do not merge simulated and physical performance tables. State actual sample size, operator and environment provenance, goal tolerances, safety interventions and failure criteria.

No physical robot was connected to this GitHub Actions experiment. **Physical-robot C01 controlled-navigation trials verified: 0.**

## Reproduction

- Source: `contributions/01_learned_astar/experiments/ros2_isolated_closed_loop.py`.
- Workflow: `.github/workflows/c01-closed-loop.yml`.
- Artifact from run 42695311932: `c01-ros2-isolated-kinematic-closed-loop` with separate JSON per mode and complete simulated pose/velocity trajectory.
- Results generated in CI are not to be treated as physical robot measurements.

**Scientific verdict:** C01 actually completes autonomous waypoint-following navigation in a ROS2-interconnected **isolated kinematic simulator** for all three algorithms; physical real-robot C01 navigation remains untested.
