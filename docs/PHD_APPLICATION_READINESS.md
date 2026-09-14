# DynNav research and engineering dossier

This page is the shortest evidence-first route through DynNav for a robotics lab, graduate admissions committee, research-engineering reviewer, or collaborator. It separates demonstrated work from claims that still require stronger execution evidence.

## Current research contribution

DynNav studies **history-conditioned safe-return planning under action-triggered topology hazards**. The central question is whether path history contains recoverability-relevant information that a state-only future-risk model discards when robot actions activate future topology hazards.

The current publication-facing contribution includes:

- a formal action-triggered closure-hazard model;
- a same-state/different-history information gap;
- exact augmented-state history-aware planning;
- a critical-cut approximation with a documented adversarial boundary;
- paired stochastic and held-out evaluations;
- three frozen hand-authored geometric held-out topologies;
- comparison against state-only and hard safe-return baselines;
- ROS 2 Jazzy / Nav2 C++ integration with persistent executed-history state;
- a frozen action-triggered Gazebo validation protocol.

Read the precise scope in the [smallest publishable core](../CORE_CONTRIBUTION.md).

## Ten-minute review path

| Time | Inspect | What it establishes |
|---:|---|---|
| 1 min | [README](../README.md) | Current question, implementation map and retained evidence snapshot |
| 2 min | [IEEE paper](../paper/dynnav_r/main.tex) | Scientific argument, baselines, results and limitations |
| 1 min | [Evidence manifest](../paper/dynnav_r/evidence_manifest.json) | Machine-readable run/artifact provenance |
| 1 min | [Claim–evidence matrix](../CLAIM_EVIDENCE_MATRIX.md) | Supported vs explicitly unsupported claims |
| 1 min | [History hazard model](../dynnav/commitment_hazard.py) | Action-triggered state semantics |
| 1 min | [Exact planner](../dynnav/planners/commitment_aware_astar.py) | Augmented `(cell, activated hazards)` search |
| 2 min | [Nav2 plugin](../ros2_ws/src/dynnav_nav2_cpp/) and [benchmark](../ros2_ws/src/dynnav_nav2_benchmark/) | ROS 2 implementation and execution-validation infrastructure |
| 1 min | [Repository guide](REPOSITORY_GUIDE.md) | Canonical paths, maturity levels and exploratory areas |

## Demonstrated capabilities

| Capability | Verifiable evidence | Boundary |
|---|---|---|
| Scientific problem formulation | Same-state/different-history construction and exact history model | Narrow action-triggered connectivity setting; not generic novelty |
| Algorithm design | Exact augmented-state planner, cut approximation, hard/state-only baselines | Cut approximation has an explicit joint-cut failure case |
| Experimental design | Paired CRN trials, analytic checks, held-out families, geometric held-out worlds, Pareto sweep | Synthetic/geometric domains remain limited |
| Statistical evaluation | Bootstrap intervals, McNemar and equivalence-test utilities, paired denominators | Results inherit scenario/model assumptions |
| Robotics integration | C++ Nav2 global planner, executed-transition history state, ROS/Gazebo benchmark infrastructure | Integration evidence is not the same as efficacy evidence |
| Reproducibility | CI on Python 3.10–3.12, paper provenance checks, retained artifacts and evidence manifest | Execution-level Gazebo history study is still pending |
| Research integrity | Explicit unsupported claims, negative cases and approximation boundary | No physical-robot efficacy or safety-certification claim |

## Retained research evidence

The strongest current publication-facing evidence includes:

- same-state histories that have different exact return probabilities while a state-only marginal model aliases them;
- controlled stochastic execution where the history-aware planner avoids the trigger mechanism;
- held-out 6/7/8-module trials with paired common random numbers;
- fork, L-room and chamber geometric held-out worlds with 500 paired seeds per scenario;
- a Pareto sweep showing hard safe-return constraints can match safe routes, preventing an overclaim that the soft objective is universally superior;
- a joint-cut counterexample that exposes where the critical-cut approximation becomes optimistic.

Authoritative numerical provenance is in `paper/dynnav_r/evidence_manifest.json`.

## Reproduce the core software evidence

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
python -m pytest -q
```

For ROS 2 Jazzy / Nav2:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

## Current evidence boundary

The history-conditioned planner is integrated into Nav2 and the first action-triggered Gazebo scenario is frozen, but comparative execution-level Gazebo efficacy is **not yet** publication evidence. Closure probabilities are model inputs rather than calibrated physical probabilities. Partial-observability, delayed-revelation and miscalibration stress tests remain future work. No physical-robot efficacy or safety-certification claim is made.

These are the next credibility jumps; adding unrelated modules is not.

## What this repository demonstrates

DynNav provides inspectable evidence of problem formulation, algorithm design, negative-case analysis, paired experimentation, statistical measurement, ROS 2/Nav2 implementation, reproducibility engineering, web/research tooling, paper authoring, and disciplined claim management. Its strongest value as a research portfolio is that the repository contains not only a proposed method, but also baselines, failure boundaries, retained evidence and explicit statements about what the evidence does **not** establish.
