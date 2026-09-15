# DynNav

**History-Conditioned Safe-Return Planning for Autonomous Robots under Action-Triggered Topology Hazards**

DynNav is a research project about autonomous navigation in environments where **what the robot has already done can change what remains safely possible later**. The repository develops the idea from a formal planning question into exact and approximate algorithms, controlled experiments, falsification tests, a C++ ROS 2/Nav2 planner, and a frozen Gazebo validation protocol.

[English](README.md) · [Ελληνικά](README_GR.md) · [Repository guide](docs/REPOSITORY_GUIDE.md) · [IEEE manuscript](paper/dynnav_r/main.tex)

[![CI](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml)
[![Paper](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB)](pyproject.toml)
[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-22314E)](ros2_ws/src/dynnav_nav2_cpp/README.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-4C1.svg)](LICENSE)

> **Research status:** active research prototype. The strongest current evidence is controlled synthetic/geometric simulation, complemented by software and ROS 2/Nav2 integration evidence. DynNav does not claim safety certification, universal planner superiority, calibrated real-world hazard probabilities, arbitrary-map generalization, or demonstrated physical-robot efficacy.

---

## The research question

This project asks:

> **When robot actions can trigger future changes in environment topology, is the robot's current geometric state sufficient for recoverability-aware planning, or must the planner also represent relevant executed-action history?**

The central observation is simple but consequential: **the same place is not always the same planning state**.

Two trajectories can reach the same cell `x` but leave different future recovery options:

```text
History A: start ── trigger ──► x     hazard activated
History B: start ── detour  ──► x     hazard not activated
```

Geometrically,

```text
x_A = x_B
```

but the safe-return probabilities can differ:

```text
P(return | x, H_A) != P(return | x, H_B)
```

A state-only model assigns one future-risk description to `x` and therefore aliases these two cases. DynNav instead uses the augmented planning state

```text
(x, H)
```

where `x` is the current grid/costmap state and `H` records hazards activated by **executed** transitions.

For two histories with true return probabilities `R1` and `R2` at the same geometric state, any single state-only estimate `g(x)` must have worst-case absolute error at least

```text
|R1 - R2| / 2
```

when `R1 != R2`. This is a representational argument: it establishes an information gap, not universal superiority of a particular planner.

This question is the mechanism behind the manuscript title **“When the Same Place Is Not the Same State.”**

---

## What I built in this project

DynNav was developed as an end-to-end research prototype rather than a single planner implementation. The work in this repository includes:

1. **Action-triggered topology hazards.** A directed executed transition can activate a stochastic future closure elsewhere in the environment. Planned paths do not activate hazards.
2. **Explicit safe-return reasoning.** For bounded hazard sets, the project computes future return-connectivity probabilities instead of relying only on local traversal-risk scores.
3. **Exact history-aware A\*.** The reference search state is `(GridCell, activated-hazard history)`, so geometrically identical cells can remain distinct when their executed histories imply different futures.
4. **Approximate online methods.** The repository implements most-reliable-return-path, hazard-disjoint-return-path, and critical-return-cut approximations for cheaper recoverability reasoning.
5. **Controlled baselines.** Shortest-path, state-only future-risk, and hard safe-return planners provide comparison points for the history-conditioned method.
6. **Same-state/different-history experiments.** These isolate the information lost when a planner compresses different histories into the same geometric state.
7. **Paired stochastic evaluation.** Common random numbers (CRN) reuse the same latent hazard realizations across planners, enabling matched comparisons rather than unrelated Monte Carlo runs.
8. **Held-out evaluations.** The project tests longer repeated-module horizons, held-out hazard probabilities, and hand-authored geometric worlds.
9. **Falsification and negative tests.** Counterexamples and controls are retained even when they weaken the preferred method or expose approximation failures.
10. **C++ ROS 2 Jazzy/Nav2 integration.** A `nav2_core::GlobalPlanner` implementation carries persistent executed-hazard history and supports controlled shortest/history-aware comparisons.
11. **Action-triggered Gazebo validation infrastructure.** The benchmark observes actual robot transitions, injects paired stochastic blockers only after valid trigger execution, checks costmaps and recovery reachability, and retains validity/provenance data.
12. **Research reproducibility infrastructure.** Deterministic seeds, statistical utilities, retained outputs, evidence manifests, claim/evidence matrices, CI checks, protocols, and regression tests connect the implementation to publication-facing claims.

The canonical Python implementations include [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py), [`dynnav/recoverability_belief.py`](dynnav/recoverability_belief.py), [`dynnav/recoverability_estimation.py`](dynnav/recoverability_estimation.py), [`dynnav/recoverability_cut.py`](dynnav/recoverability_cut.py), and [`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py).

---

## What the project shows

The strongest supported conclusion is deliberately narrower than “this planner is always better”:

> **When executed actions can alter future topology, path history can contain recoverability-relevant information that cannot, in general, be represented by geometric state alone.**

The same-state/different-history construction demonstrates this directly. The controlled execution experiments then test whether the representational difference can affect decisions.

### Retained mechanism evidence

| Study | State-only / shortest | Exact history-aware | Scope |
|---|---:|---:|---|
| 3-module execution, `p=0.8` | 0.992 failure | 0.000 | controlled mechanism |
| Held-out 6 modules | 0.992 | 0.000 | repeated-module horizon extension |
| Held-out 7 modules | 0.998 | 0.000 | repeated-module horizon extension |
| Held-out 8 modules | 1.000 | 0.000 | repeated-module horizon extension |
| Fork | 0.810 | 0.000 | frozen hand-authored topology |
| L-room | 0.756 | 0.000 | frozen hand-authored topology |
| Chamber | 0.890 | 0.000 | frozen hand-authored topology |

The larger-module and geometric studies use **500 paired CRN seeds per reported scenario**. These results show the mechanism within the tested constructed families. They do not establish arbitrary-map or broad real-world generalization.

The geometric cases also probe different reasons for selecting a safer route: a longer safe branch in the fork, trigger avoidance without a longer final path in the L-room, and a safe detour in the chamber environment.

Authoritative publication-facing values and provenance are retained in [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json).

---

## What we learned when the preferred method did not win

Negative results are part of the project rather than being removed from the evidence trail.

A soft history-aware objective does **not** universally dominate a hard safe-return constraint. In tested cases, hard thresholds can select the same zero-hazard route and can sometimes have lower single-run planning latency. The contribution is therefore not universal dominance of one objective; it is the need to represent relevant history when history changes future recoverability.

The critical-cut approximation is also **not exact**. A retained joint-cut counterexample contains two parallel return corridors. Neither closure is individually critical, but the two closures together eliminate safe return. With independent closure probability `p`, the exact return probability is

```text
P(safe return) = 1 - p^2
```

so for `p = 0.2, 0.5, 0.8` the exact values are `0.96, 0.75, 0.36`. A single-critical-cut approximation remains optimistic and disagrees with the exact calculation across the tested counterexample settings.

These failures narrow the scientific claim and make the distinction between the **history-conditioned representation** and any particular approximation or objective explicit.

---

## Core model

### Action-triggered topology hazards

The reference semantics are implemented in [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py):

```text
(source -> target)  =>  activate hazard h
```

Planning, execution, activation, and realization are deliberately separate:

```text
transition planned
      |
transition executed
      |
hazard activated
      |
closure may or may not realize
```

**Planned paths never activate hazards.** Persistent history changes only when the corresponding transition is actually executed.

### Exact safe-return probability

For bounded hazard sets, DynNav enumerates future closure realizations and checks connectivity to a designated safe region. The target quantity is

```text
R(x, H) = P(safe return | x, H)
```

rather than a generic local risk score.

### History-aware planning

The exact reference planner [`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py) searches over

```text
(GridCell, frozenset[activated hazard indices])
```

and augments nominal transition cost with a recoverability term based on

```text
1 - P(safe return | next state, activated history)
```

| Planner | Role |
|---|---|
| Shortest path | geometric baseline |
| State-only hazard/reliability planner | marginal future-risk baseline |
| Exact history-aware planner | augmented-state reference method |
| Critical-cut planner | faster approximation |
| Hard safe-return planner | probability-threshold baseline |

---

## Experimental methodology

The evaluation is built around matched comparisons and retained evidence. It includes paired common-random-number comparisons, deterministic seed policies, exact McNemar tests for paired binary outcomes, paired bootstrap confidence intervals, equivalence/non-inferiority utilities where appropriate, operational mission/recovery/failure labels, timing and path metrics, frozen configurations, and machine-readable provenance.

When planners share a generated world or latent event realization, analysis uses the paired denominator rather than treating rows as independent observations.

The current experiment contract is [`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md). The historical J0-J3 protocol is retained in [`docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md`](docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md) as research history rather than the current paper claim.

Publication-facing experiment families include same-state/different-history information-gap constructions, analytic commitment phase boundaries, stochastic commitment execution, critical-cut scaling, held-out probability/horizon tests, geometric held-out worlds (`fork`, `l_room`, `chamber_two_trigger`), the joint-cut adversarial counterexample, and soft-history versus hard-safe-return Pareto sweeps.

---

## ROS 2 / Nav2 implementation

The publication-facing C++ package is [`ros2_ws/src/dynnav_nav2_cpp`](ros2_ws/src/dynnav_nav2_cpp). It includes:

- augmented `(costmap cell, activated-hazard bitmask)` search state;
- exact small-hazard return-connectivity enumeration;
- `initial_active_mask` support for replanning after previous triggers;
- soft history-aware transition costs;
- proactive trigger-avoidance tests;
- same-cell/different-history reliability tests;
- retained-history online replanning tests.

The Nav2 plugin implements `nav2_core::GlobalPlanner` and exposes shortest/history modes through the same implementation.

### Executed-history semantics

Persistent state is updated from actual execution rather than planned geometry. The plugin subscribes to

```text
dynnav/executed_transition
```

with transitions encoded as

```text
sx:sy>tx:ty
```

This prevents a planned-but-never-executed route from incorrectly modifying the future environment state.

---

## Action-triggered Gazebo protocol

The benchmark package [`ros2_ws/src/dynnav_nav2_benchmark`](ros2_ws/src/dynnav_nav2_benchmark) provides Gazebo blocker injection, Nav2 execution, planner-path observation, global-costmap snapshots, blocker validation, independent recovery-reachability checks, failure/validity labels, retained traces, hashes, and balanced planner ordering.

The frozen scenario is configured in [`sandbox_history_triggered_events.yaml`](ros2_ws/src/dynnav_nav2_benchmark/config/sandbox_history_triggered_events.yaml) and documented in [`ACTION_TRIGGER_PROTOCOL.md`](ros2_ws/src/dynnav_nav2_benchmark/ACTION_TRIGGER_PROTOCOL.md).

The first frozen trigger is

```text
(174,189) -> (175,189)
```

with closure cell `(181,191)` and declared closure probability `p = 0.8`.

Protocol rules require that trigger credit comes only from observed consecutive robot states; same-cell samples are ignored; observation gaps are reported rather than interpolated; the latent closure draw is paired across planners; the blocker moves only if the trigger was actually observed and the latent closure realizes; trigger avoidance is valid; and planned geometry never activates the hazard.

This protocol is execution-level research infrastructure, not a claim of completed physical-robot validation.

---

## Falsification, scope, and limitations

DynNav intentionally retains tests that weaken or delimit the preferred method. The falsification suite includes:

- same-state/same-history controls;
- reverse-direction trigger controls;
- sampling and trigger-observation gaps;
- unrealized stochastic events;
- false-conservatism cases;
- hard-constraint equivalence;
- critical-cut joint failures;
- probability miscalibration;
- correlated closures;
- delayed hazard revelation;
- kinodynamic-model mismatch;
- geometric-generalization limits.

These tests distinguish cases where history conditioning is representationally necessary from cases where a simpler state representation, hard constraint, or approximation may be sufficient.

DynNav does **not** currently establish:

- formal safety guarantees or safety certification;
- universal planner superiority;
- calibrated real-world closure probabilities;
- arbitrary-map or broad real-world generalization;
- collision-avoidance or kinodynamic completeness of the grid model;
- physical-robot efficacy or hardware reliability;
- exactness of the critical-cut approximation;
- dominance of the soft objective over hard safe-return constraints.

The strongest current empirical evidence is controlled synthetic/geometric simulation with retained reproducible artifacts, complemented by software and ROS 2/Nav2 integration evidence.

---

## Research evolution

DynNav began with the broader J0-J3 risk/recoverability-aware replanning framework:

- **J0:** shortest path;
- **J1:** path length + traversal risk;
- **J2:** path length + structural recoverability penalty;
- **J3:** path length + risk + recoverability.

That work established deterministic replanning, dynamic route invalidation, risk-aware scoring, operational recovery definitions, paired evaluation, artifact retention, and failure taxonomies.

The project then narrowed the publication-facing question: vague structural recoverability was replaced by explicit future-connectivity probability; action-triggered hazards were introduced; same-state/different-history aliasing was isolated; exact augmented-state planning and critical-cut approximations were implemented; counterexamples and held-out evaluations were added; and the mechanism was transferred to ROS 2/Nav2 with executed-history semantics.

Historical protocols and audits remain under [`docs/archive/`](docs/archive/) for provenance. They are research history, not the current paper claim.

---

## Quick start

### Python

DynNav requires Python 3.10 or newer.

```bash
git clone https://github.com/panagiotagrosdouli/DynNav.git
cd DynNav
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"
python -m pytest -q
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
```

On Windows, activate with `.venv\Scripts\activate`.

Available entry points include `dynnav-demo` and `dynnav-benchmark`.

### ROS 2 Jazzy / Nav2

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

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

The repository also contains historical prototypes and exploratory modules. Their presence does not imply equal validation maturity or support for the current paper claims. See [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) for the canonical map.

---

## Evidence hierarchy and reproducibility

| Level | Meaning |
|---|---|
| A | deterministic implementation/unit-test evidence |
| B | controlled mechanism evidence |
| C | retained comparative stochastic/geometric evidence |
| D | ROS 2/Nav2 integration evidence |
| E | execution-level validation under frozen protocol contracts |

Key evidence documents:

- [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) — authoritative numerical provenance;
- [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) — supported, partial, and unsupported claims;
- [`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md) — current experiment semantics;
- [`FAILURE_CASES.md`](FAILURE_CASES.md) — falsification and negative cases.

The manuscript and evidence pipeline are CI-checked so publication-facing numerical claims remain tied to retained artifacts.

---

## Reviewer path

For a fast technical review:

1. [`paper/dynnav_r/main.tex`](paper/dynnav_r/main.tex) — scientific argument and results.
2. [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) — artifact/run provenance.
3. [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) — supported vs. unsupported claims.
4. [`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md) — experiment semantics.
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

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

---

## Policies and supporting documents

[Repository guide](docs/REPOSITORY_GUIDE.md) · [Claims](CLAIM_EVIDENCE_MATRIX.md) · [Current protocol](EXPERIMENT_PROTOCOL_V3.md) · [Failure cases](FAILURE_CASES.md) · [Research archive](docs/archive/README.md) · [Contributing](CONTRIBUTING.md) · [Citation](CITATION.cff) · [Security](SECURITY.md) · [License](LICENSE)
