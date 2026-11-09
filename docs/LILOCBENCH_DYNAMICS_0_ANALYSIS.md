# LILocBench `dynamics_0` Ground-Truth Trajectory Analysis

This is a descriptive analysis of the public recorded ground-truth poses for the LILocBench `dynamics_0` sequence. The sequence is a real Clearpath Dingo indoor recording with moving people. LILocBench reports this sequence as approximately 10 people moving near the robot and provides ground-truth poses for it. Ground truth is obtained with ceiling AprilTags and is expressed in the common global frame.

## Measured summary

| Measure | Value |
|---|---:|
| Ground-truth pose samples | 3,194 |
| Duration | 159.951 s |
| Mean sample frequency | 19.962 Hz |
| Sample interval | 0.050 s minimum; 0.050 s median; 0.150 s maximum |
| XY path length | 53.967 m |
| Start-to-end XY displacement | 7.954 m |
| Mean XY speed (path length / duration) | 0.337 m/s |
| Median per-segment XY speed | 0.378 m/s |
| 95th percentile per-segment XY speed | 0.440 m/s |
| Maximum per-segment XY speed | 1.102 m/s |
| X bounds | -0.537 m to 10.822 m |
| Y bounds | -9.429 m to -3.555 m |

Speeds use Euclidean distance between consecutive XY ground-truth positions divided by their timestamp interval. Path length is the sum of those segment distances. These are trajectory-description statistics, not localization error, planner performance, route success, or evidence that a scene change caused the robot to replan.

## Reproduce from the source

Download the public `dynamics_0` ground-truth pose file from the official dataset page, then run:

```bash
python scripts/analyze_lilocbench_ground_truth.py /path/to/gt_poses.txt \
  --output results/real_data/lilocbench_dynamics_0_summary.json
```

The JSON records the SHA-256 digest of the exact input file, sample timing, spatial bounds, and trajectory statistics. The source file is distributed by LILocBench under CC BY-NC-SA 4.0. Do not commit or redistribute the raw dataset file; include the attribution and license terms when sharing adaptations.

The plot below shows the recorded XY path only. It is not drawn over the LILocBench occupancy grid.

## Attribution and source

N. Trekel, T. Guadagnino, T. Läbe, L. Wiesmann, P. Aguiar, J. Behley, and C. Stachniss, “Benchmark for Evaluating Long-Term Localization in Indoor Environments Under Substantial Static and Dynamic Scene Changes,” *Proc. IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*, 2025.

- [Official LILocBench dataset page](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/)
- [Public `dynamics_0` ground-truth poses](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/gt_poses_public/dynamics_0/gt_poses.txt)
