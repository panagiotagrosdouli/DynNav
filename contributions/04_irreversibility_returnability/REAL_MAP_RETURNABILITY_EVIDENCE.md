# C04: Verified real-office returnability and ROS2 planning evidence

**Recorded 2026-11-09.** The underlying LILocBench office occupancy geometry is real. Starts and goals are generated offline, and the environment was not traversed by a robot under C04 control.

## Reproducible real-map experiment

[Successful GitHub Actions run #42712603647](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42712603647) downloaded and SHA-256-verified the real 1000 x 1000 LILocBench office map at 0.05 meters/cell, then ran 4 *identical paired* planning tasks for three algorithms. The trusted return base was defined explicitly as the starting cell of each query.

| Algorithm | Found | Mean route steps | Mean peak geometric irreversibility proxy |
|---|---:|---:|---:|
| Unconstrained Manhattan A* | 4/4 | 275.75 | 0.357121 |
| Original C04 hard cap tau=0.08 | 0/4 | — | — |
| Exact minimax feasible C04 cap | 4/4 | 278.75 | 0.115899 |

The actual computed minimum feasible per-task thresholds were **0.0972424, 0.1056017, 0.1666293 and 0.0941209**. The C04 constrained route increased the mean path length by 3 cells (1.09%) compared with the paired shortest-route baseline. These 4 cases are a *pilot*, not general performance evidence.

The geometric proxy for a free cell was defined as:

    I(x) = 0.50 * clip(return_distance_to_base / (map_width + map_height), 0, 1)
         + 0.30 * (1 - four_connected_free_neighbor_count / 4)
         + 0.20 * exp(-obstacle_clearance_cells / 5)

It is **not** a calibrated probability, a formal safety shield or a physically measured irreversible transition. Static undirected occupancy cells are mechanically reversible under the idealized grid motion model; the score only measures geometric fragility. A physically closed door or non-holonomic dynamics could invalidate the assumed return path.

The exact minimax solver computes the least achievable maximum fragility along any four-connected route, rather than using a coarse threshold grid. All twelve trial rows passed path and threshold checks. The reproducibility artifact is named **c04-real-office-geometric-returnability-and-minimax-threshold** and includes trials.csv, summary.json and map hashes.

## ROS 2 Jazzy actual GetPlan service

[Successful ROS 2 run #42712664962](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42712664962) executed a real ROS 2 Jazzy GetPlan request-response between nodes using a synthetic 12x12 OccupancyGrid. Three modes were exercised:

- NORMAL: permissive tau=1.0 returns a valid plan
- SAFE_RELAX_TAU: a restrictive tau=0.08 with permitted relaxation returns a path at the computed minimum feasible threshold
- SAFE_STOP: tau=0.08 with zero permitted relaxation returns **no path**, rather than violating the limit

This shows real ROS 2 middleware and the C04 planning/diagnostic code operating, not movement, Nav2 controller integration, Gazebo or physical validation. No actuation was issued.

## Confirmed historical defect and repair

The prior safe-mode threshold sweep could omit the exact tau_max endpoint when the interval was not divisible by tau_step. This could falsely reject an otherwise feasible route. The code now checks the exact endpoint and fails closed on invalid or nonfinite threshold/mapping inputs. Dedicated regression tests exercise the omitted-endpoint case and unsafe relaxation.

## Reproduce

Run the dedicated workflow .github/workflows/c04-real-office-returnability.yml or execute:

    python contributions/04_irreversibility_returnability/experiments/eval_real_office_returnability.py /path/to/map_office.yaml --output-dir results/c04_real_office --tasks 4 --seed 17 --tau .08

For live ROS 2 message tests, run .github/workflows/c04-ros2-returnability.yml. These workflows upload actual machine-readable result artifacts.

## Research limitations

One real static map and four generated queries do not show physical recoverability, uncertain perception, action-triggered hazards, independent-map generalization, or kinodynamic feasibility. Hardware safety needs independently commissioned ROS 2/Nav2 control, actual trustworthy ground truth and synchronized physical robot trajectory evidence.

**Verified physical C04-controlled robot trials: 0.**
