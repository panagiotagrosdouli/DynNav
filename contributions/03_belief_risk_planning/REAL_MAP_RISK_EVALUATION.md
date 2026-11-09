# C03 — Executed real occupancy-map route risk evaluation (2026-11-09)

## Genuine executed evidence

[Verified successful real-map GitHub Actions run #42707934764](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42707934764), using the institutional LILocBench office occupancy map (1000 x 1000 grid cells, 0.05 m/cell) originally mapped with a physical Clearpath Dingo. The workflow checked the downloaded official archive SHA-256, parsed the original ROS YAML + image, and ran **five identical randomly generated, reachable start-goal queries** with both distance-only and risk-weighted A*.

**The robot never drove these generated routes.** The risk values were calculated solely from **distance to static mapped obstacles**, not learned or physically calibrated accident probabilities.

## Results actually measured in CI

| Mean over 5 paired queries | Distance-only A* | Additive proximity-risk A* |
|---|---:|---:|
| Geometric path length (cells) | 327.0 | 341.8 |
| Mean obstacle-proximity proxy on chosen route | 0.436083 | 0.078008 |
| Upper-tail empirical CVaR of proxy (alpha=0.90) | 0.814889 | 0.251391 |
| Expanded nodes | 11,178.2 | 15,904.2 |
| Measured search time on CI runner | 23.38 ms | 35.48 ms |

The risk-weighted algorithm selected a route with ~4.5% higher average length, substantially smaller proximity penalty, and increased average search work. **Do not claim this is an actual reduction in real-world collision probability.**

### Optimized objective vs evaluation metrics

The planner minimizes the **additive** map proxy objective

```
J(path) = sum_edges [1 + lambda * exp(-distance_to_nearest_obstacle_cells / decay)]
```

with lambda=8 and decay=5 cells. The route CVaR is computed **after** the path is selected, with a fractional-boundary exact empirical upper tail. This is **NOT a solver that minimizes CVaR**, and it does not integrate calibrated C02 localization uncertainty, dynamic hazards, or action-triggered recoverability theory.

## Reproduction and traceability

Original source map: https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/

The dedicated workflow `.github/workflows/c03-real-office-risk.yml` downloads the real map, verifies archive SHA-256 `941f96bf90d7d89dddf76fb4864f45212318d39f2b4f1220318786e53f48f6b0`, then runs:

```bash
python contributions/03_belief_risk_planning/experiments/eval_real_map_proximity_risk.py \
  /path/to/map_office.yaml \
  --output-dir results/c03_real_map \
  --seed 17 --n-tasks 5 --risk-weight 8 --alpha 0.9
```

The workflow artifact `c03-lilocbench-real-office-proximity-risk-astar` contains `trials.csv` (10 actual measurements) and `summary.json` (exact map hashes, dimensions, parameters, evidence class, zero physical trials). Its independent CI checker verifies paired starts/goals, valid routes, shortest-length baseline and declared additive objective.

Regression tests in `tests/test_real_map_proximity_risk.py` verify fractional empirical CVaR, cost-optimal route search on a synthetic test grid and disconnected path rejection. Existing C03/C10 cost and ethical-risk composition tests run in the same workflow.

## Remaining scientific and hardware barriers

- The original Dingo data collection did NOT select routes using C03.
- No C03 closed-loop robot command, real LiDAR risk distribution, actual navigation success rate or physical observation ground-truth comparison has been obtained.
- No real-world calibrated hazard probabilities; the proxy is obstacle distance only.
- No optimization of full trajectory-level CVaR across stochastic motion/occupancy scenarios.
- No formal guarantee that a particular risk reduction meets real-world safety thresholds.

**Verified physical robot C03 trials: zero.**

Stronger claims require calibrated perception and uncertainty, risk-scenario distributions, independent maps and obstacle dynamics, paired ROS2 controllers, reliable safety instrumentation and new authenticated physical robot runs.
