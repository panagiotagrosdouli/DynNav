# Experiment Protocol V2

## Preregistration and data split

Use disjoint deterministic seed lists for development (0–49), tuning (10,000–10,099), blinded pilot/power estimation (20,000–20,049), and final evaluation (30,000 onward). Freeze maps, weights, thresholds, event rules, margins, exclusions, and analysis before revealing evaluation labels. Never tune on final scenarios.

## Factorial benchmark

Scenario families:

1. `open_neutral`: high clearance, no meaningful escape contrast; shortest should win on overhead.
2. `risk_dominant`: alternative routes differ in costmap risk but have matched recovery feasibility; J1 should win.
3. `recovery_dominant`: matched length/risk, different retreat feasibility after a randomized event; J2 should win.
4. `risk_recovery_aligned`: one route is both lower-risk and more recoverable; J3 should not be worse than components.
5. `risk_recovery_conflict`: low-risk/low-recovery versus higher-risk/high-recovery; tests the joint trade-off.
6. `false_conservatism`: narrow passage is necessary and never invalidated; J2 overhead without benefit is measured.
7. `deceptive_local_degree`: side pockets raise local escape count but do not connect to a safe region; attacks the current heuristic.
8. `retreat_closure`: obstacle appears behind the commitment surface.
9. `forward_closure`: negative control; retreat remains open.
10. `moving_crossing`: dynamic obstacle changes the live perception/costmap and later clears.

Orthogonally sample: corridor width `{0.45, 0.60, 0.90, 1.20} m`; alternative-route overhead `{0, 5, 10, 20, 40}%`; risk contrast `{0, 0.1, 0.25, 0.5}` normalized score units; event probability `{0, 0.25, 0.5, 0.75}`; observation delay `{0.2, 0.5, 1.0, 2.0}s`; commitment depth `{0.2, 0.5, 0.8}` of corridor; localization noise `{nominal, medium, high}` using sensor/localization configuration, not ground-truth input. Use a balanced fractional factorial design if the full crossing is too large.

## Planners and fairness

Run NavFn, Smac2D, J0, J1, J2, and J3 with identical map, robot, localization, costmaps, controller, behavior tree, recovery behaviors, goal, event schedule, and seed. Change only planner ID/weights. Counterbalance planner order in complete blocks. Reset simulator and Nav2 state between trials. Trigger events at a spatial commitment surface with a maximum-time fallback; log achieved state. Invalid observation trials are rerun only under a frozen replacement-seed rule and remain in the audit table.

## Sample size

Start with a blinded 50-seed pilot per scenario-condition block to estimate the paired discordance rate, not efficacy. Compute the final sample for exact McNemar power 0.8, two-sided familywise alpha 0.05 after Holm correction, targeting an absolute irreversible-failure reduction of 10 percentage points. Until pilot estimates exist, budget **100 paired seeds per planner per primary family×uncertainty cell**. Do not claim that 100 is guaranteed adequate; report the power calculation and increase when discordant pairs are sparse.

## Primary estimand and analysis

Primary estimand: paired risk difference in post-invalidation recovery-infeasible failure, J2 versus J0 and J3 versus J1, on valid final-evaluation trials. Report exact McNemar p-values, paired bootstrap 95% CIs, and discordant-pair counts. Fit a mixed-effects logistic model with planner, uncertainty, family, and planner×uncertainty interaction, with seed/map random intercepts. Treat it as supportive if convergence/assumptions fail.

Secondary outcomes: mission/recovery success; path-length ratio; initial/replan latency; replan count; navigation duration; collision; minimum clearance; cumulative risk; minimum/AUC recoverability. Report mean, median, SD, IQR, and bootstrap 95% CIs. For H3 use two one-sided non-inferiority tests against frozen margins of 15% executed-path overhead and 25 ms median replan-latency overhead (revise only before evaluation, based on application requirements).

Correct four primary contrasts with Holm. Label all family-specific and failure-mode analyses exploratory unless preregistered.

## Required outputs

Plots: paired outcome transition plot; failure rate with Wilson CI; risk-difference forest plot; overhead ECDF/violin; planner-latency distribution; planner×uncertainty interaction; Pareto failure-versus-overhead plot; validity/exclusion flow; and synchronized failure-case panels showing world truth, robot-visible costmap, pre/post paths, event, and recoverable region.

Tables: configuration; scenario balance; validity/exclusions; primary binary effects; secondary outcomes; H3 non-inferiority; failure taxonomy; and sensitivity analyses.

## Run artifact contract

Each trial directory must contain `manifest.json`, exact command, Git SHA/dirty flag, container digest and package versions, seed, planner parameters, map/world/event snapshot, start/goal, timestamps, stdout/stderr/ROS logs, raw metrics, pre/post planner paths, costmap snapshots, validity reason, and rosbag metadata. Record `/tf`, `/tf_static`, `/odom`, `/scan`, `/cmd_vel`, localization, global/local costmaps, planner path, behavior-tree status, action feedback/result, and event-service calls. Every figure receives a sidecar manifest listing raw input hashes and generation command.

## Minimum ROS execution commands

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --symlink-install
source install/setup.bash
colcon test
colcon test-result --verbose

ros2 launch dynnav_nav2_benchmark tb3_static_planner_benchmark.launch.py \
  headless:=true repetitions:=10 output_dir:=$PWD/results/nav2_static
ros2 launch dynnav_nav2_benchmark tb3_dynamic_execution_benchmark.launch.py \
  headless:=true repetitions:=100 output_dir:=$PWD/results/nav2_dynamic
```

The dynamic launch is now configured for all six planners, direct `/plan`
instrumentation, pre-event path-intersection validation, and rosbag capture.
These contracts still require execution on a ROS 2 Jazzy/Gazebo machine before
they satisfy the Level 4 evidence requirement.
