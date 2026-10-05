# DynNav — Project Overview

## What DynNav studies

DynNav is a research project on **history-conditioned safe-return planning under action-triggered topology hazards**. Its central observation is that two robot executions can reach the same geometric cell while having different future return-connectivity because earlier **executed actions** activated different stochastic closure hazards.

The publication-facing planning state is therefore not position alone. Under the finite hazard model used by the current paper, the sufficient statistic is `(grid cell, activated hazard set)`. This is standard state augmentation / Markovization; the contribution is the explicit action-triggered return-topology formulation, its controlled information-gap construction, and the measured behavior of exact and approximate planners under that formulation.

## Current research question

> Does executed path history carry recoverability-relevant information that an endpoint-only fixed-field representation discards when robot actions activate future topology hazards?

DynNav does **not** claim that history-aware planning, MDP state augmentation, safe-return constraints, or generic recoverability are new.

## Canonical system

The current publication path contains:

1. **Action-triggered hazard semantics** — directed executed transitions activate stochastic future closures.
2. **Exact safe-return probability** — bounded hazard sets are evaluated by enumerating future closure realizations and checking connectivity to a designated safe region.
3. **Exact history-aware A\*** — search over `(cell, activated hazards)`.
4. **Baselines** — geometric shortest/NavFn, state-only marginal/exact fixed-field controls, and hard safe-return constraints.
5. **Approximation** — critical-cut planning with both a series-critical regime where it is exact and a retained joint-cut counterexample where it is optimistic.
6. **Paired evaluation** — common-random-number stochastic studies, held-out horizon/probability cases, frozen hand-authored topologies, and objective-form sensitivity.
7. **ROS 2 / Nav2** — a C++17 `nav2_core::GlobalPlanner` with persistent history updated from executed transitions rather than from planned paths.
8. **Gazebo validation** — a frozen action-triggered mechanism protocol with retained strict integration probes and explicit validity/exclusion rules.
9. **Evidence discipline** — machine-readable provenance, claim/evidence mapping, failure cases, and publication-facing limitations.

## Evidence currently retained

The strongest comparative evidence remains controlled synthetic/geometric evaluation. Retained studies include the same-state/different-history information-gap construction, analytic commitment phase-boundary checks, paired stochastic execution, held-out module/probability studies, three frozen hand-authored geometries, exact state-only fixed-field controls, a 96-scenario unavoidable-hazard expansion, exact-vs-critical-cut scaling, a joint-cut adversarial counterexample, and soft-objective versus hard-safe-return Pareto sweeps.

The ROS/Gazebo evidence establishes software integration and protocol-valid execution. Retained strict mechanism probes have valid end-to-end trials and successful navigation across the frozen planner conditions, but the DynNavHistory-vs-DynNavShortest trigger-exposure difference is not stable across reruns. Therefore **comparative Gazebo efficacy is not a supported claim**.

Authoritative numerical provenance is in [paper/dynnav_r/evidence_manifest.json](../paper/dynnav_r/evidence_manifest.json), and claim boundaries are in [CLAIM_EVIDENCE_MATRIX.md](../CLAIM_EVIDENCE_MATRIX.md).

## Publication-facing execution semantics

A planned path may reason about future triggers, but it does not mutate persistent hazard history. Only observed execution does. The sequence is: executed transition → trigger observation → activated hazard history → safe-return model → history-conditioned search → ROS 2/Nav2 execution → retained evidence.

## What is canonical and what is exploratory

The canonical publication path is described in [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md). The main paths are:

```text
dynnav/                              Python research core
  planners/                          exact, approximate and baseline planners
  experiments/                       controlled and held-out studies
  evaluation/                        metrics/statistics

ros2_ws/src/dynnav_nav2_cpp/         C++ Nav2 planner
ros2_ws/src/dynnav_nav2_benchmark/   ROS/Gazebo benchmark contracts
paper/dynnav_r/                       manuscript + evidence manifest
results/                              retained outputs
scripts/                              reproducible runners and audits
tests/                                regression/research-contract tests
configs/                              frozen configuration
app/                                  Streamlit research lab
apps/api/ + apps/web/                 research API/workspace
contributions/                        exploratory programme; not paper evidence
```

Historical J0–J3 risk/recoverability experiments and broader exploratory modules remain useful research history, but they are **not** the current central paper claim.

## Reproduce the core

Python:

```bash
python -m pip install -e ".[dev,researcher,dashboard]"
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
python -m pytest -q
python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/ci_smoke
python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/ci_benchmarks
```

ROS 2 Jazzy / Nav2:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

Web surfaces use committed npm lockfiles and clean `npm ci` installs.

## Reviewer reading path

1. [README.md](../README.md)
2. [CORE_CONTRIBUTION.md](../CORE_CONTRIBUTION.md)
3. [CLAIM_EVIDENCE_MATRIX.md](../CLAIM_EVIDENCE_MATRIX.md)
4. [EXPERIMENT_PROTOCOL_V3.md](../EXPERIMENT_PROTOCOL_V3.md)
5. [FAILURE_CASES.md](../FAILURE_CASES.md)
6. [paper/dynnav_r/evidence_manifest.json](../paper/dynnav_r/evidence_manifest.json)
7. [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)
8. [ros2_ws/src/dynnav_nav2_cpp](../ros2_ws/src/dynnav_nav2_cpp)
9. [ros2_ws/src/dynnav_nav2_benchmark](../ros2_ws/src/dynnav_nav2_benchmark)

## Current boundary

DynNav does not establish formal safety certification, calibrated real-world hazard probabilities, arbitrary-map generalization, universal superiority, or physical-robot efficacy. The next scientific hardening targets are probability-miscalibration, partial-observability/delayed-revelation stress tests, broader predeclared geometry families, and—only if an execution-efficacy claim is desired—a broader powered Gazebo study.

A release candidate should be frozen only after the repository's full-main audit, paper build, final bibliography review, and number-to-evidence-manifest verification all pass.
