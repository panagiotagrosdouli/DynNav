# DynNav

**History-conditioned safe-return planning for autonomous robots under action-triggered topology hazards.**

DynNav studies a specific dynamic-navigation failure mode: two executions can reach the **same geometric state** while having different future recoverability because earlier robot actions activated different environmental hazards.

[English](README.md) · [Ελληνικά](README_GR.md) · [Repository guide](docs/REPOSITORY_GUIDE.md) · [IEEE paper](paper/dynnav_r/main.tex)

[![CI](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml)
[![Paper](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB)](pyproject.toml)
[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-22314E)](ros2_ws/src/dynnav_nav2_cpp/README.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-4C1.svg)](LICENSE)

> **Status:** active research prototype with retained synthetic/geometric evidence, an integrated C++ Nav2 planner, and a frozen action-triggered Gazebo protocol. No safety-certification, universal-superiority, or physical-robot efficacy claim is made.

## Research question

> **Does path history carry recoverability-relevant information that a state-only future-risk model discards when robot actions activate future topology hazards?**

The publication-facing planner reasons over an augmented state:

```text
(grid cell, activated hazard history)
```

Persistent hazard history is updated from **executed transitions**, never from imagined/planned transitions.

## What is implemented

| Layer | Implementation |
|---|---|
| Planning | shortest, risk-aware, exact history-aware, critical-cut and hard safe-return planners |
| Hazard model | directed action-triggered stochastic topology closures |
| Recoverability | exact future-closure oracle plus online approximations |
| Evaluation | paired common-random-number trials, bootstrap intervals, McNemar/TOST utilities |
| ROS 2 / Nav2 | C++17 `nav2_core::GlobalPlanner` with persistent executed-history state |
| Gazebo | static, time-triggered dynamic and frozen action-triggered protocols |
| Paper | IEEE manuscript with machine-readable evidence manifest and provenance checks |
| Interfaces | Streamlit lab plus FastAPI / Next.js research workspace |

The older J0–J3 risk/recoverability family remains as an earlier controlled research layer. The current paper contribution is the narrower **history-conditioned safe-return** problem.

## Retained evidence snapshot

| Study | State-only / shortest | History-conditioned | Scope |
|---|---:|---:|---|
| 3-module execution, `p=0.8` | 0.992 failure | 0 failure | controlled mechanism |
| Held-out 6/7/8 modules | 0.992 / 0.998 / 1.000 | 0 / 0 / 0 | probability/horizon generalization |
| Fork / L-room / chamber | 0.810 / 0.756 / 0.890 | 0 / 0 / 0 | three frozen hand-authored topologies |
| Joint-cut counterexample | — | cut approximation disagrees with exact in 9/9 settings | explicit failure boundary |

The geometric Pareto study also showed that hard safe-return constraints can match the safe route in these worlds. The supported result is therefore about the **history representation**, not a universal claim that a soft objective dominates hard constraints.

Authoritative provenance and manuscript-facing values live in [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) and [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md).

## Paper

**When the Same Place Is Not the Same State: History-Conditioned Safe-Return Planning under Action-Triggered Topology Hazards**

The contribution is deliberately narrow: action-triggered degradation of return-connectivity, same-state/different-history aliasing, exact augmented-state planning, a fast critical-cut approximation with a documented adversarial boundary, held-out evaluation, and ROS 2/Nav2 integration.

Generic recoverability, safe-return constraints, history-dependent costs, and decision-dependent uncertainty are **not** claimed as novel.

## Reviewer path

1. [`paper/dynnav_r/main.tex`](paper/dynnav_r/main.tex) — paper argument and results.
2. [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) — run/artifact provenance.
3. [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) — canonical code and evidence map.
4. [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) — supported/partial/unsupported claims.
5. [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py) — trigger-history model.
6. [`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py) — exact reference planner.
7. [`ros2_ws/src/dynnav_nav2_cpp`](ros2_ws/src/dynnav_nav2_cpp) — C++ Nav2 planner.
8. [`ros2_ws/src/dynnav_nav2_benchmark`](ros2_ws/src/dynnav_nav2_benchmark) — ROS/Gazebo validation.

## Canonical repository map

```text
dynnav/                         Python research core
ros2_ws/src/dynnav_nav2_cpp/    C++ Nav2 planner
ros2_ws/src/dynnav_nav2_benchmark/ ROS/Gazebo benchmark
paper/dynnav_r/                  IEEE paper + evidence manifest
results/                         retained experiment outputs
scripts/                         reproducible runners and audits
tests/                           regression/research-contract tests
configs/                         experiment configuration
docs/                            scientific + engineering documentation
app/                             Streamlit research lab
apps/api/ + apps/web/            research API/workspace
contributions/                   exploratory programme; not paper evidence
```

Older top-level modules remain for compatibility and historical experiments. They are not all part of the canonical paper path; see the repository guide before treating them as validated contributions.

## Reproduce the Python core

```bash
git clone https://github.com/panagiotagrosdouli/DynNav.git
cd DynNav
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
python -m pytest -q
```

## ROS 2 Jazzy / Nav2

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

The first action-triggered Gazebo scenario was frozen before comparative outcomes: trigger `(174,189) -> (175,189)`, closure cell `(181,191)`, declared closure probability `0.8`. New Gazebo efficacy claims should be added only after retained execution artifacts pass the protocol validity checks.

## Evidence discipline

A publication-facing claim requires implementation, deterministic regression coverage, frozen configuration/seed policy, retained machine-readable output, provenance, appropriate paired/statistical analysis, and an explicit limitation or failure boundary.

Strongest current evidence is simulation/grid based. The next hardening step is retained action-triggered Gazebo execution with paired planner conditions, followed by partial-observability and probability-miscalibration stress tests if that execution evidence is valid.

## Policies

[Repository guide](docs/REPOSITORY_GUIDE.md) · [Claims](CLAIM_EVIDENCE_MATRIX.md) · [Protocol](EXPERIMENT_PROTOCOL_V2.md) · [Failure cases](FAILURE_CASES.md) · [Contributing](CONTRIBUTING.md) · [Citation](CITATION.cff) · [Security](SECURITY.md) · [License](LICENSE)
