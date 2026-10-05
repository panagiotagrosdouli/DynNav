# DynNav technical documentation

This directory documents the current publication-facing DynNav research program:

> **History-conditioned safe-return planning under action-triggered topology hazards.**

The central question is whether executed action history can carry recoverability-relevant information that an endpoint-only, state-only marginal model discards when robot actions activate future topology hazards.

## Primary research thread

For the current paper and evidence boundary, read in this order:

1. [`../README.md`](../README.md): project summary, quick start, retained evidence and limitations.
2. [`REPOSITORY_GUIDE.md`](REPOSITORY_GUIDE.md): canonical code/evidence map and maturity boundaries.
3. [`../CORE_CONTRIBUTION.md`](../CORE_CONTRIBUTION.md): smallest publishable contribution.
4. [`../CLAIM_EVIDENCE_MATRIX.md`](../CLAIM_EVIDENCE_MATRIX.md): supported, partial and unsupported claims.
5. [`../EXPERIMENT_PROTOCOL_V3.md`](../EXPERIMENT_PROTOCOL_V3.md): current history-conditioned experimental semantics and validity rules.
6. [`../FAILURE_CASES.md`](../FAILURE_CASES.md): negative results, counterexamples and falsification cases.
7. [`../paper/dynnav_r/evidence_manifest.json`](../paper/dynnav_r/evidence_manifest.json): authoritative numerical provenance.
8. [`MATHEMATICAL_FORMULATION.md`](MATHEMATICAL_FORMULATION.md): planning, risk and safe-return formulation.
9. [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md): seeds, commands, configurations and artifact traceability.
10. [`../PUBLICATION_READINESS.md`](../PUBLICATION_READINESS.md): current release/submission gate.

The earlier J0–J3 recoverability/risk program is retained as research history. Its protocol lives in [`archive/EXPERIMENT_PROTOCOL_V2_J0J3.md`](archive/EXPERIMENT_PROTOCOL_V2_J0J3.md) and must not be treated as the current paper claim.

## Architecture and implementation references

- [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md): package ownership and component boundaries.
- [`NAVIGATION_PIPELINE.md`](NAVIGATION_PIPELINE.md): observation, planning, monitoring and replanning flow.
- [`REPOSITORY_GUIDE.md`](REPOSITORY_GUIDE.md): canonical Python, ROS 2/Nav2, experiment and evidence paths.
- [`ROS2_HISTORY_VALIDATION_PROTOCOL.md`](ROS2_HISTORY_VALIDATION_PROTOCOL.md): executed-history validation semantics.
- [`GAZEBO_BENCHMARK_PROTOCOL.md`](GAZEBO_BENCHMARK_PROTOCOL.md): Gazebo benchmark contracts and evidence limits.
- [`MARKDOWN_STYLE_GUIDE.md`](MARKDOWN_STYLE_GUIDE.md): maturity vocabulary and claim discipline.

## Current planner comparison

Publication-facing history-conditioned studies use the smallest comparison set required by the research question:

| Planner / baseline | Scientific role |
|---|---|
| shortest / NavFn | geometric reference |
| state-only marginal return-risk | endpoint-only ablation that omits activated-hazard history |
| exact history-aware | augmented-state reference planner over position and activated hazards |
| critical-cut history approximation | faster approximation with an explicit joint-cut failure boundary |
| hard safe-return threshold | feasibility-style baseline for objective-form comparison |

The state-only baseline is deliberately restricted. Its failure does not establish superiority over a general MDP/POMDP that retains the active hazard process.

## Evidence levels

DynNav separates implementation from empirical evidence:

- deterministic unit and contract tests establish local implementation behavior;
- controlled constructions establish the history-information mechanism;
- paired stochastic and held-out studies establish results only in their frozen synthetic/geometric families;
- ROS 2/Nav2 build, plugin and execution tests establish integration;
- retained Gazebo mechanism probes establish end-to-end execution and measurement validity, not a stable comparative efficacy effect;
- physical-robot efficacy, safety certification and broad real-world generalization are not currently supported.

Numerical publication claims should be checked against [`../paper/dynnav_r/evidence_manifest.json`](../paper/dynnav_r/evidence_manifest.json) before reuse.

## Verified commands

From the repository root:

```bash
python -m pip install -e ".[dev,researcher,dashboard]"
python -m pytest -q
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/ci_smoke
python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/ci_benchmarks
```

For the publication-facing Nav2 packages on ROS 2 Jazzy:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

Dashboard:

```bash
streamlit run app/dashboard.py
```

## Secondary and historical material

The repository contains exploratory modules in learning, prediction, security, multi-robot coordination, semantic navigation, formal shields and other earlier research tracks. Their presence is useful for research history but does not make them evidence for the current paper.

Use [`CONTRIBUTION_FEATURE_CATALOG.md`](CONTRIBUTION_FEATURE_CATALOG.md) for the broader catalog and [`archive/README.md`](archive/README.md) for historical research documents.

## Evidence policy

Implementation is not equivalent to experimental proof. Passing tests establishes consistency with the implemented contract; synthetic experiments support only the evaluated assumptions and scenario families. Any stronger claim requires separately retained evidence with frozen configuration, seeds, validity rules, provenance and an explicit limitation boundary.
