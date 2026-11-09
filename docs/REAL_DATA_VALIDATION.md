# Real-Data Validation Plan

This plan adds a real-world evidence track while preserving the current claim boundary. Public logs can validate map ingestion, localization inputs, and observed environmental change. They do not provide a controlled counterfactual comparison of DynNav against baselines under action-triggered closures.

## Public dataset: LILocBench

Use the public sequences from the [LILocBench dataset](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/). It was recorded with a Clearpath Dingo in an indoor office and provides a ROS map-server occupancy map, ROS bags, and ground-truth poses for selected sequences.

Recommended first download:

1. The occupancy map and its YAML metadata.
2. `mapping` and `dynamics_0` for a static-versus-moving-people replay.
3. `lt_changes_0` for a known environment-change sequence with public ground truth.
4. `lt_changes_3` only as an explicitly unlabeled closed-door stress case; the dataset does not publish ground-truth poses for this sequence.

The no-camera bags for the first three recommended sequences are much smaller than the full dataset. Download the exact files from the upstream page; do not commit the dataset or redistribute derived copies. LILocBench uses CC BY-NC-SA 4.0, so cite Trekel et al. (IROS 2025) and retain the non-commercial/share-alike conditions for any adapted dataset material.

After installing DynNav with `python -m pip install -e .`, inspect the supplied occupancy map and optionally check a route whose endpoints are given in map-frame metres:

```bash
python scripts/inspect_ros_map.py /path/to/map.yaml --start 1.0,2.0 --goal 7.0,4.0
```

The command prints the map image SHA-256, geometry, unknown-cell policy, and (when endpoints are supplied) baseline A* reachability and path length. Record the chosen endpoints and keep the upstream map unchanged for a reproducible comparison.

## What this dataset can establish

- Whether DynNav can ingest the real occupancy map with correct origin, resolution, image-axis direction, and conservative unknown-cell handling.
- Whether observed robot trajectories and dynamic-scene sequences can be replayed against that map without frame or coordinate errors.
- Whether a recorded scene change alters free-space connectivity or route feasibility under the declared map-generation procedure.

It cannot establish that the robot's own actions caused those scene changes, nor compare counterfactual planner outcomes on the same physical event. Keep these results separate from the action-triggered hazard efficacy claims in the paper.

## Physical robot study

The repository's [hardware checklist](HARDWARE_VALIDATION_CHECKLIST.md) remains the commissioning protocol. After the base, localization, costmaps, and emergency stop pass commissioning:

1. Freeze one map, start/goal set, planner configurations, trigger transition, remotely operated lightweight closure, and outcome definitions before collecting comparison trials.
2. Randomize planner order within matched blocks. Reset the robot and closure between trials, and log the same closure-event identity across each matched block.
3. Credit a trigger only from adjacent executed poses, never from a planned path. Record the closure command, costmap observation, post-event pose, recovery feasibility, mission result, and invalid-trial reason.
4. Retain every protocol-valid failure. Report paired risk differences with confidence intervals and exact paired tests; determine sample size from a separate pilot before opening the evaluation run.
5. Stop on any checklist stop criterion. Do not test near people or use an obstacle that can injure the robot or operator.

Required run metadata: robot and sensor identifiers, ROS distribution and package versions, map hash, source Git SHA, planner parameters, route and trigger coordinates, trial order, event seed or event identity, rosbag URI, validity, incident notes, and analysis version.

## Evidence status

A first descriptive analysis of the public `dynamics_0` ground-truth trajectory has been completed and is recorded in [LILocBench dynamics_0 analysis](LILOCBENCH_DYNAMICS_0_ANALYSIS.md). It covers 3,194 poses over 159.951 seconds: 53.967 m of XY path and 0.337 m/s mean XY speed. The [website plot](../website/public/lilocbench-dynamics-0-ground-truth.svg) is the measured XY trajectory without an occupancy-map background.

The analyzer records a SHA-256 digest when run against the downloaded original pose file. The map ZIP, ROS-bag replay, and planner comparisons have not yet been run or retained as result artifacts. The trajectory statistics describe the recorded robot motion; they do not show that DynNav caused, avoided, or recovered from any event. Passing map-import or playback checks is engineering validation. Planner-efficacy claims require valid controlled comparisons with traceable outcomes. Physical-robot efficacy remains pending matched trials under the frozen protocol.

## Citation

N. Trekel, T. Guadagnino, T. L\"abe, L. Wiesmann, P. Aguiar, J. Behley, and C. Stachniss, “Benchmark for Evaluating Long-Term Localization in Indoor Environments Under Substantial Static and Dynamic Scene Changes,” *Proc. IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*, 2025. See the [dataset page](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/) for the BibTeX record and data license.
