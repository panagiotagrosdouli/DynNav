# DynNav Reproducibility Report

**Status:** core CI/research stack verified; execution-level history-conditioned Gazebo validation remains pending.

## Verified repository state

| Item | Value |
|---|---|
| Date | 2026-09-14 |
| Repository | `panagiotagrosdouli/DynNav` |
| Default branch | `main` |
| Organized research-core merge | `7e655b7d6e282fef0274e1ee88106ecc2022e499` |
| Last pre-organization fully green main CI | run `34831325240` |
| Python matrix | 3.10 / 3.11 / 3.12 |
| ROS 2 | Jazzy |
| Nav2 plugin build/discovery | verified in CI |
| Website/researcher web builds | verified in CI |
| Documentation inventory/link audit | verified in CI |

The repository uses GitHub-hosted clean runners as the authoritative clean-checkout environment. This supersedes the older local DNS-blocked clone attempt that was previously recorded here.

## Core Python verification

CI installs the canonical package from the repository and verifies that imports resolve to `dynnav/`. It then runs Ruff, mapping-core type checks, the unified regression suite, reproducibility smoke checks and benchmark smoke checks according to the Python-version matrix.

Local equivalent:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
python -m pytest -q
```

## ROS 2 / Nav2 verification

The CI container builds the Jazzy Nav2 plugin and checks planner discovery/configuration. The history-conditioned C++ planner is integrated into `main`; persistent activated-hazard history is updated from executed-transition input rather than from the nominal planned path.

Representative local workflow:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

Build/discovery success is an integration claim, not an execution-efficacy claim.

## Publication evidence reproducibility

The publication-facing provenance source is:

`paper/dynnav_r/evidence_manifest.json`

Retained experiment families include the history information gap, analytic phase boundary, stochastic commitment execution, cut scaling, held-out probability/horizon study, joint-cut counterexample, geometric held-out benchmark and geometric Pareto sweep.

Numerical manuscript claims should be sourced from retained artifacts referenced by that manifest rather than copied from ad-hoc console output.

## Paper verification

The paper workflow validates evidence provenance, compiles the IEEE manuscript, rejects unresolved references/citations and uploads the compiled PDF artifact. The manuscript is located at:

`paper/dynnav_r/main.tex`

## Web and dashboard verification

The main CI validates the website and researcher workspace dependency graphs, audits dependencies, type-checks and builds both web surfaces. The Streamlit workflow validates dashboard structure/imports, runs smoke tests and checks a headless health endpoint.

## Full-repository workflow audit

`.github/workflows/full-main-audit.yml` provides a repository-level mechanism for dispatching manually runnable research/evidence workflows on `main`. Path-triggered and push-triggered workflows retain their normal contracts.

A workflow success demonstrates that its declared checks passed for that run; it does not automatically promote exploratory modules to publication evidence.

## Remaining reproducibility boundary

The action-triggered Gazebo validation protocol is frozen but comparative history-conditioned execution outcomes are not yet part of the manuscript evidence. The first frozen event uses directed trigger `(174,189) -> (175,189)`, closure cell `(181,191)` and declared closure probability `0.8`.

Before reporting Gazebo efficacy, retained trials must verify:

- an adjacent executed trigger transition was actually observed;
- the paired stochastic event realization was applied consistently across planners;
- the physical blocker injection succeeded when required;
- the blocker became visible in the relevant costmap;
- recovery feasibility and irreversible-failure labels were computed under the frozen contract;
- invalid trials were reported separately.

## Claim boundary

Passing reproducibility and CI checks does not establish safety certification, physical-robot efficacy, calibrated real-world closure probabilities, universal planner superiority or broad real-world generalization. See `CLAIM_EVIDENCE_MATRIX.md` for the current supported/unsupported claim boundary.
