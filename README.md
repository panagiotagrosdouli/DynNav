# DynNav

**Author:** Panagiota Grosdouli

**History-Conditioned Safe-Return Planning for Autonomous Robots under Action-Triggered Topology Hazards**

> **Same place does not always mean the same planning state.**

DynNav studies autonomous navigation in environments where a robot's **executed actions can change future topology**. Two trajectories can end at the same geometric location while leaving the robot with different safe-return options because one trajectory activated a future hazard and the other did not.

[English](README.md) · [Ελληνικά](README_GR.md) · [Repository guide](docs/REPOSITORY_GUIDE.md) · [IEEE manuscript](paper/dynnav_r/main.tex)

[![CI](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml)
[![Paper](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB)](pyproject.toml)
[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-22314E)](ros2_ws/src/dynnav_nav2_cpp/README.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-4C1.svg)](LICENSE)

## The idea in 20 seconds

Consider two histories that reach the same cell:

```text
History A: start ── trigger ──► x     hazard activated
History B: start ── detour  ──► x     hazard not activated
```

Both robots are at the same geometric state `x`, but they do not necessarily have the same future:

```text
x_A = x_B

P(return | x, H_A) ≠ P(return | x, H_B)
```

A planner that reasons only about position aliases these cases. DynNav instead plans over the augmented state

```text
(position, activated-hazard history) = (x, H)
```

so the consequences of **what the robot actually executed** remain part of the planning problem.

## Why this matters

A shortest path can be attractive now while committing the robot to a future topology change that makes safe return impossible if a closure realizes. DynNav explicitly reasons about this commitment instead of treating future hazard probability as a state-only map.

The project asks a narrow research question:

> **Does executed path history contain recoverability-relevant information that a state-only future-risk model discards when robot actions activate future topology hazards?**

## What is implemented

- **Exact history-aware A\*** over `(grid cell, activated hazards)`
- **Exact safe-return probability** for bounded hazard sets
- **State-only, shortest-path, hard safe-return, and approximation baselines**
- **Critical-cut approximation** with retained counterexamples showing where it fails
- **Paired stochastic and held-out geometric evaluation**
- **C++ ROS 2 Jazzy / Nav2 global planner**
- **Persistent executed-history tracking**: planned paths do not activate hazards
- **Gazebo benchmark infrastructure** for action-triggered topology changes
- **Reproducible evidence pipeline** with frozen protocols, statistical tests, negative results, and explicit limitations

## Representative evidence

In the retained constructed evaluations, the exact history-aware planner avoids action-triggered closures that cause high irreversible-failure rates for shortest/state-only planning:

| Scenario | Shortest / state-only failure | Exact history-aware failure |
|---|---:|---:|
| 3-module execution, `p=0.8` | 0.992 | 0.000 |
| Held-out 6 modules | 0.992 | 0.000 |
| Fork topology | 0.810 | 0.000 |
| L-room topology | 0.756 | 0.000 |
| Chamber topology | 0.890 | 0.000 |

These are **mechanism-level results in controlled synthetic/geometric environments**, not evidence of universal planner superiority or real-world safety.

An important negative result is retained as well: hard safe-return constraints can match the zero-hazard behavior of the soft history-aware objective in some tested environments. The main contribution is therefore the **history-conditioned state representation and action-triggered return-connectivity model**, not a claim that one objective always wins.

## From research model to robotics stack

```text
Executed robot motion
        │
        ▼
Directed trigger detection
        │
        ▼
Activated hazard history H
        │
        ├──────────────► Safe-return model R(x, H)
        │                         │
        ▼                         ▼
   Nominal cost ─────────► History-aware search
                                  │
                                  ▼
                            ROS 2 / Nav2
                                  │
                                  ▼
                         Gazebo validation
```

The ROS 2 implementation preserves hazard history from **executed transitions**, not from paths that were merely planned. This distinction is part of the core semantics of DynNav.

## Quick start

### Python

```bash
git clone https://github.com/panagiotagrosdouli/DynNav.git
cd DynNav
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"

dynnav-demo
```

Run the regression suite:

```bash
python -m pytest -q
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
```

### ROS 2 Jazzy / Nav2

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

> **Research status:** DynNav is an active research prototype. It does not claim safety certification, arbitrary-map generalization, calibrated real-world hazard probabilities, universal planner superiority, or demonstrated physical-robot efficacy.

---

## Core model

### Action-triggered topology hazards

The reference semantics are implemented in [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py). A directed transition can activate a stochastic future closure elsewhere in the environment:

```text
(source -> target)  =>  activate hazard h
```

The semantics deliberately separate planning, execution, activation, and realization:

```text
transition planned
      |
transition executed
      |
hazard activated
      |
closure may or may not realize
```

**Planned paths never activate hazards.** Persistent hazard history changes only when the corresponding transition is actually executed.

### Exact safe-return probability

For bounded hazard sets, DynNav enumerates possible future closure realizations and checks connectivity to a designated safe region. The reference implementation is primarily in:

- [`dynnav/recoverability_belief.py`](dynnav/recoverability_belief.py)
- [`dynnav/recoverability_estimation.py`](dynnav/recoverability_estimation.py)
- [`dynnav/recoverability_cut.py`](dynnav/recoverability_cut.py)

The target quantity is

```text
R(x, H) = P(safe return | x, H)
```

rather than a generic local risk score.

### History-aware planning

The exact reference planner is [`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py). Its search state is

```text
(GridCell, frozenset[activated hazard indices])
```

and its soft objective augments nominal transition cost with a recoverability term based on

```text
1 - P(safe return | next state, activated history)
```

The main planner families are:

| Planner | Role |
|---|---|
| Shortest path | geometric baseline |
| State-only hazard/reliability planner | marginal future-risk baseline |
| Exact history-aware planner | augmented-state reference method |
| Critical-cut planner | faster approximation |
| Hard safe-return planner | probability-threshold baseline |

The soft history-aware objective is **not** assumed to dominate every alternative. Hard safe-return constraints can match or outperform it in some tested environments.

---

## Main contributions

DynNav provides:

1. an action-triggered topology-hazard model in which executed robot transitions can change the distribution of future connectivity;
2. a constructive same-state/different-history example showing that equal geometric states can have different exact safe-return probabilities;
3. an augmented-state history-aware planner;
4. an exact future-connectivity oracle for bounded hazard sets;
5. critical-cut and related online approximations;
6. adversarial counterexamples that expose approximation failure boundaries;
7. paired stochastic evaluation using common random numbers (CRN);
8. held-out horizon/probability and hand-authored geometric evaluations;
9. a C++ ROS 2 Jazzy/Nav2 implementation with persistent executed-history state;
10. a frozen action-triggered Gazebo protocol and explicit validity rules;
11. a claim-evidence/falsification pipeline linking publication-facing claims to retained artifacts and limitations.

---

## Key retained evidence

| Study | State-only / shortest | Exact history-aware | Scope |
|---|---:|---:|---|
| 3-module execution, `p=0.8` | 0.992 failure | 0.000 | controlled mechanism |
| Held-out 6 modules | 0.992 | 0.000 | repeated-module horizon extension |
| Held-out 7 modules | 0.998 | 0.000 | repeated-module horizon extension |
| Held-out 8 modules | 1.000 | 0.000 | repeated-module horizon extension |
| Fork | 0.810 | 0.000 | frozen hand-authored topology |
| L-room | 0.756 | 0.000 | frozen hand-authored topology |
| Chamber | 0.890 | 0.000 | frozen hand-authored topology |

The larger-module and geometric studies use 500 paired CRN seeds per reported scenario. These results are evidence for the mechanism **within the tested constructed families**; they are not evidence of universal or arbitrary-map generalization.

### Important negative result

The geometric Pareto study showed that hard safe-return constraints can also select zero-hazard routes and can have lower single-run planning latency in some cases. The supported contribution is therefore about **history-conditioned state representation and action-triggered return-connectivity**, not universal superiority of the soft objective.

The critical-cut approximation also has an explicit joint-failure counterexample: with two parallel return corridors and independent closure probability `p`, exact return probability can be `1 - p^2` while a single-critical-cut approximation remains optimistic. This failure case is intentionally retained.

Authoritative paper-facing values and provenance live in [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json).

---

## Quick start

### Python

DynNav requires Python 3.10 or newer and is configured for Python 3.10, 3.11, and 3.12.

```bash
git clone https://github.com/panagiotagrosdouli/DynNav.git
cd DynNav
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

Available package entry points include:

```bash
dynnav-demo
dynnav-benchmark
```

Run the regression suite and lint checks with:

```bash
python -m pytest -q
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
```

### ROS 2 Jazzy / Nav2

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

---

## Experimental methodology

The evaluation stack is designed around matched comparisons and retained evidence rather than isolated demo runs. It includes:

- paired common-random-number comparisons;
- deterministic seed policies;
- exact McNemar tests for paired binary outcomes;
- paired bootstrap confidence intervals;
- equivalence/non-inferiority utilities where appropriate;
- operational mission/recovery/failure labels;
- path-length, latency, replanning and risk measurements;
- frozen configurations and machine-readable artifacts;
- provenance manifests tying reported values to retained outputs.

When planners share a generated world or latent event realization, analysis uses the paired denominator rather than treating rows as independent observations.

The current experiment contract is [`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md). The historical J0-J3 protocol is retained under [`docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md`](docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md) as research history rather than as the current paper claim.

### Main experiment families

The publication-facing evaluation includes:

- same-state/different-history information-gap construction;
- analytic commitment phase-boundary tests;
- stochastic commitment execution;
- critical-cut scaling;
- held-out probability/horizon generalization;
- geometric held-out topologies (`fork`, `l_room`, `chamber_two_trigger`);
- joint-cut adversarial counterexample;
- soft-history versus hard-safe-return Pareto sweeps.

Experiment implementations live primarily in [`dynnav/experiments/`](dynnav/experiments/) and reproducible runners in [`scripts/`](scripts/).

---

## ROS 2 / Nav2 implementation

The publication-facing C++ package is [`ros2_ws/src/dynnav_nav2_cpp`](ros2_ws/src/dynnav_nav2_cpp).

The C++ core includes:

- augmented `(costmap cell, activated-hazard bitmask)` search state;
- exact small-hazard return-connectivity enumeration;
- `initial_active_mask` support for replanning after previous triggers;
- soft history-aware transition cost;
- proactive trigger-avoidance tests;
- same-cell/different-history reliability tests;
- retained-history online replanning tests.

The Nav2 plugin implements `nav2_core::GlobalPlanner` and exposes shortest/history modes through the same implementation for controlled comparisons.

### Executed-history semantics

Persistent state is updated from actual execution rather than planned geometry. The plugin subscribes to

```text
dynnav/executed_transition
```

with transitions encoded as

```text
sx:sy>tx:ty
```

This prevents a planned-but-never-executed path from incorrectly modifying the future environment state.

---

## Action-triggered Gazebo protocol

The benchmark package is [`ros2_ws/src/dynnav_nav2_benchmark`](ros2_ws/src/dynnav_nav2_benchmark). It supports Gazebo blocker injection, Nav2 execution, planner-path observation, global-costmap snapshots, blocker-observation validation, independent recovery-reachability checks, validity/exclusion labels, retained traces, and balanced planner ordering.

The frozen action-triggered scenario is defined in [`sandbox_history_triggered_events.yaml`](ros2_ws/src/dynnav_nav2_benchmark/config/sandbox_history_triggered_events.yaml) and documented in [`ACTION_TRIGGER_PROTOCOL.md`](ros2_ws/src/dynnav_nav2_benchmark/ACTION_TRIGGER_PROTOCOL.md).

The first frozen trigger is

```text
(174,189) -> (175,189)
```

with closure cell `(181,191)` and declared closure probability `p = 0.8`.

Protocol rules include:

- trigger credit only from observed consecutive states quantizing to the configured directed adjacent cells;
- same-cell samples are ignored;
- observation gaps are reported and never interpolated;
- the latent closure draw is paired across planners;
- the physical blocker moves only when the trigger is observed and the paired latent closure realizes;
- trigger avoidance is a valid planner outcome;
- planned geometry never activates the hazard.

The frozen protocol should not be confused with a claim of completed physical-robot or broad real-world efficacy.

---

## Repository structure

```text
dynnav/                             Python research core
  planners/                         exact/approximate/baseline planners
  experiments/                      controlled and held-out studies
  evaluation/                       statistics and outcome metrics

ros2_ws/src/dynnav_nav2_cpp/        C++ Nav2 history-aware planner
ros2_ws/src/dynnav_nav2_benchmark/  ROS/Gazebo validation infrastructure
paper/dynnav_r/                      IEEE manuscript + evidence manifest
results/                             retained experiment outputs
scripts/                             reproducible runners and audits
tests/                               regression/research-contract tests
configs/                             experiment configuration
docs/                                scientific + engineering documentation
docs/archive/                        historical protocols/audits
app/                                 Streamlit research lab
apps/api/ + apps/web/                research API/workspace
contributions/                       exploratory programme; not paper evidence
```

The repository contains historical prototypes and exploratory modules in addition to the canonical publication path. Their presence does **not** imply equal validation maturity or support for the current paper claims. See [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) for the authoritative code/evidence map.

---

## Evidence hierarchy and reproducibility

DynNav distinguishes implementation from empirical evidence:

| Level | Meaning |
|---|---|
| A | deterministic implementation/unit-test evidence |
| B | controlled mechanism evidence |
| C | retained comparative stochastic/geometric evidence |
| D | ROS 2/Nav2 integration evidence |
| E | execution-level validation under frozen protocol contracts |

A publication-facing claim is expected to have implementation, regression coverage, frozen configuration/seed policy, retained machine-readable output, provenance, appropriate paired/statistical analysis, and an explicit limitation or failure boundary.

Key evidence documents are:

- [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) — authoritative numerical provenance;
- [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) — supported, partial and unsupported claims;
- [`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md) — current experiment semantics;
- [`FAILURE_CASES.md`](FAILURE_CASES.md) — falsification and negative cases.

The manuscript and evidence pipeline are CI-checked so publication-facing numerical claims remain tied to retained artifacts.

---

## Failure cases and limitations

DynNav intentionally retains tests that weaken or delimit the preferred method. The falsification suite includes same-state/same-history controls, reverse-direction trigger controls, sampling gaps, unrealized events, false conservatism, hard-constraint equivalence, critical-cut joint failures, probability miscalibration, correlated closures, delayed revelation, kinodynamic mismatch, and geometric-generalization limits.

DynNav does **not** currently establish:

- formal safety guarantees or safety certification;
- universal planner superiority;
- calibrated real-world closure probabilities;
- arbitrary-map or broad real-world generalization;
- collision-avoidance or kinodynamic completeness of the grid model;
- physical-robot efficacy or hardware reliability;
- exactness of the critical-cut approximation;
- dominance of the soft objective over hard safe-return constraints.

The strongest current empirical evidence is controlled synthetic/geometric simulation, complemented by software and ROS integration evidence.

---

## Research evolution

DynNav began with a broader J0-J3 risk/recoverability-aware replanning framework and progressively narrowed its publication-facing question. Early work established deterministic replanning, dynamic route invalidation, risk-aware scoring, operational recovery definitions, paired evaluation, artifact retention, and failure taxonomies.

The project then replaced vague structural recoverability with explicit future-connectivity probability, introduced action-triggered hazards, demonstrated same-state/different-history aliasing, implemented augmented-state planning, added approximation counterexamples and held-out evaluations, and transferred the mechanism into ROS 2/Nav2.

Historical protocols and audits remain under [`docs/archive/`](docs/archive/) for provenance. They should not be interpreted as the current paper claim.

---

## Reviewer path

For a fast technical review, read in this order:

1. [`paper/dynnav_r/main.tex`](paper/dynnav_r/main.tex) — scientific argument and results.
2. [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) — artifact/run provenance.
3. [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) — supported vs. unsupported claims.
4. [`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md) — current experiment semantics.
5. [`FAILURE_CASES.md`](FAILURE_CASES.md) — falsification and negative cases.
6. [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py) — action-trigger model.
7. [`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py) — exact reference planner.
8. [`ros2_ws/src/dynnav_nav2_cpp`](ros2_ws/src/dynnav_nav2_cpp) — C++ Nav2 implementation.
9. [`ros2_ws/src/dynnav_nav2_benchmark`](ros2_ws/src/dynnav_nav2_benchmark) — ROS/Gazebo benchmark.
10. [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) — canonical repository map.

---

## Paper and citation

The current manuscript is [`paper/dynnav_r/main.tex`](paper/dynnav_r/main.tex):

> **When the Same Place Is Not the Same State: History-Conditioned Safe-Return Planning under Action-Triggered Topology Hazards**

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Please use that file for the repository's current citation metadata rather than copying author/version information from secondary documentation.

---

## Policies and supporting documents

[Repository guide](docs/REPOSITORY_GUIDE.md) · [Claims](CLAIM_EVIDENCE_MATRIX.md) · [Current protocol](EXPERIMENT_PROTOCOL_V3.md) · [Failure cases](FAILURE_CASES.md) · [Research archive](docs/archive/README.md) · [Contributing](CONTRIBUTING.md) · [Citation](CITATION.cff) · [Security](SECURITY.md) · [License](LICENSE)
