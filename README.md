# DynNav: Uncertainty-Aware Risk-Sensitive Navigation for Unknown Environments

Companion repository for ongoing research on uncertainty-aware, risk-sensitive planning for mobile robot navigation in previously unmapped environments.

**Author:** Panagiota Grosdouli, Department of Electrical & Computer Engineering, Democritus University of Thrace

---

## Abstract

Mobile robots operating in unknown environments must plan under uncertainty about both the map and their own state estimate. Standard shortest-path planners treat this uncertainty implicitly, if at all, and offer no formal guarantee against unsafe outcomes. This repository implements and evaluates a navigation stack that (i) maintains an explicit belief over occupancy and robot state, (ii) plans routes that trade off path cost against a risk measure (Conditional Value-at-Risk) derived from that belief, and (iii) enforces hard safety constraints at execution time via a Signal Temporal Logic monitor and Control Barrier Function command filter. The stack is evaluated in simulation (Gazebo, ROS 2 Humble) and, for a subset of components, on a TurtleBot3 Burger.

## Research Motivation

Classical planners (A*, D*) assume a known or fully-observed cost map and offer no explicit treatment of state or map uncertainty. In unknown environments this assumption fails: occupancy estimates are noisy and incomplete, and a planner that ignores this can select paths that are nominally short but carry high probability of collision or entrapment. This work asks how uncertainty can be represented, propagated into planning, and bounded by formal safety guarantees, without prohibitive computational cost for on-board deployment.

## Research Objectives

1. Represent environment and state uncertainty in a form usable by a real-time planner.
2. Quantify and incorporate risk (not just expected cost) into route selection.
3. Provide a formal, verifiable safety layer independent of the planner's own correctness.
4. Evaluate the resulting stack's safety–efficiency trade-off against classical baselines, in simulation and on hardware.

## Research Questions

- **RQ1:** Does incorporating a CVaR risk term over predicted occupancy uncertainty reduce collision/entrapment rate relative to expected-cost planning, and at what path-length cost?
- **RQ2:** Can a lightweight learned heuristic reduce planning-time node expansions without degrading the risk-awareness of the resulting path?
- **RQ3:** Does an independent STL+CBF safety shield reduce constraint violations beyond what the risk-aware planner achieves alone, and what is the resulting control overhead?

## Methodology

Uncertainty over occupancy is estimated from LiDAR/SLAM output using an Extended/Unscented Kalman Filter for state estimation and a diffusion-based predictive model for occupancy in unobserved regions. Planning uses a risk-weighted A* variant that optimizes a CVaR objective over the resulting occupancy distribution, subject to a returnability constraint that avoids irreversible dead-ends. A learned heuristic is used to reduce planner node expansions. At execution time, a Signal Temporal Logic monitor checks safety specifications online and a Control Barrier Function filter modifies commands minimally when a violation is imminent.

## System Architecture

```
Perception            LiDAR SLAM, EKF/UKF state estimation
        |
Environment Rep.       Diffusion-based occupancy uncertainty map
        |
Planning               Risk-weighted A* (CVaR), returnability constraint,
                        learned heuristic
        |
Execution Safety       STL monitor -> CBF command filter
        |
Actuation               ROS 2 Humble -> TurtleBot3 / Gazebo
```

## Repository Structure

```
dynnav/
├── experiments/                  # One directory per evaluated experiment
│   ├── 01_learned_astar/
│   ├── 02_uncertainty_estimation/
│   ├── 03_belief_risk_planning/
│   ├── 04_irreversibility_returnability/
│   ├── 05_safe_mode_navigation/
│   ├── 07_next_best_view/
│   ├── 12_diffusion_occupancy/
│   ├── 18_formal_safety_shields/
│   └── tests/
├── core/                         # Shared planning primitives
├── dynamic_nav/                  # Main ROS 2 navigation stack
├── lidar_ros2/                   # LiDAR + SLAM integration
├── configs/                      # Experiment configuration files (version-controlled)
├── docs/                         # Method notes, per-experiment README
├── exploratory/                  # Early-stage work outside current scope (see note below)
├── requirements.txt
├── CITATION.cff
└── README.md
```

> **Note on `exploratory/`:** earlier iterations of this repository additionally explored vision-language mission parsing, reinforcement learning, federated/multi-robot consensus, adversarial robustness, and neuromorphic sensing. These are retained under `exploratory/` as early-stage, unvalidated experiments and are explicitly **not** part of the current research claim. They may form the basis of future work (§ Future Research Directions) but should not be read as completed contributions.

## Experimental Pipeline

Each experiment directory contains a single entry-point script producing a CSV/plot output under `results/`, and a fixed random seed set. Example:

```bash
python experiments/18_formal_safety_shields/eval_safety_shields.py \
    --n_episodes 50 --seed 0 --out_csv results/shield_eval.csv
```

All reported numbers in this README are regenerated by `scripts/run_all_experiments.py`, which is exercised by continuous integration on every push (see badge below).

## Current Development Status

| Experiment | Status | Evaluated on |
|---|---|---|
| Uncertainty estimation (EKF/UKF) | Implemented, evaluated | Simulation |
| Diffusion occupancy maps | Implemented, evaluated | Simulation |
| Belief-space / CVaR risk planning | Implemented, evaluated | Simulation |
| Irreversibility / returnability | Implemented, evaluated | Simulation |
| Safe-mode navigation | Implemented, evaluated | Simulation + hardware (limited trials) |
| Learned A* heuristic | Implemented, evaluated | Simulation |
| Next-best-view exploration | Implemented, evaluated | Simulation |
| Formal safety shields (STL+CBF) | Implemented, evaluated | Simulation |

No component in this list is described as "tested on hardware" unless a specific hardware trial log exists under `results/hardware/`.

## Evaluation Strategy

Each experiment is run for a fixed number of episodes with fixed seeds; reported metrics include mean and standard deviation across seeds, not point estimates alone. Baselines are classical (non-risk-aware) equivalents of each component, run under identical scenario generation. Scenario generators and seeds are version-controlled under `configs/` so results are exactly reproducible from a clean checkout.

## Future Research Directions

The following are open questions, not implemented capabilities:

- Extending the risk-aware planner to multi-robot settings, where consensus under partial observability becomes relevant.
- Evaluating whether vision-language grounding can provide semantically meaningful exploration priorities without compromising the safety guarantees of the STL/CBF layer.
- Assessing robustness of the diffusion-based occupancy predictor under sensor spoofing or adversarial perturbation.
- Real-time performance characterization for on-board (non-workstation) compute.

## References

A full bibliography is maintained in `docs/references.bib`. Core methodological references (CVaR optimization, Control Barrier Functions, Signal Temporal Logic monitoring, EKF/UKF state estimation) are cited in each experiment's `README.md`.

## Citation

```bibtex
@software{grosdouli2026dynnav,
  author  = {Grosdouli, Panagiota},
  title   = {{DynNav}: Uncertainty-Aware Risk-Sensitive Navigation for Unknown Environments},
  year    = {2026},
  url     = {https://github.com/panagiotagrosdouli/dynnav},
  license = {Apache-2.0}
}
```

## License

Apache License, Version 2.0 — see `LICENSE`.
