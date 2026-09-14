# DynNav

**History-conditioned safe-return planning for autonomous robots under action-triggered topology hazards.**

DynNav is a research and engineering repository about a specific failure mode in autonomous navigation: two executions can reach the **same geometric state** while having different future recoverability because earlier robot actions activated different environmental hazards.

The repository started as a broader risk/recoverability-aware replanning project and was progressively narrowed, tested, falsified, reimplemented, and integrated into ROS 2/Nav2 around one publication-facing question:

> **Does path history carry recoverability-relevant information that a state-only future-risk model discards when robot actions activate future topology hazards?**

[English](README.md) · [Ελληνικά](README_GR.md) · [Repository guide](docs/REPOSITORY_GUIDE.md) · [IEEE paper](paper/dynnav_r/main.tex)

[![CI](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/ci.yml)
[![Paper](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/paper-build.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB)](pyproject.toml)
[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-22314E)](ros2_ws/src/dynnav_nav2_cpp/README.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-4C1.svg)](LICENSE)

> **Status:** active research prototype with retained synthetic/geometric evidence, an integrated C++ Nav2 planner, a frozen action-triggered Gazebo protocol, and an IEEE-style manuscript/evidence pipeline. No safety-certification, universal-superiority, calibrated real-world probability, or physical-robot efficacy claim is made.

---

## What we built in this repository

DynNav is not just one planner file. The repository now contains a complete research stack covering formulation, algorithms, baselines, experiments, statistical analysis, ROS integration, simulation validation, evidence tracking, publication artifacts, and explicit failure cases.

### 1. We started from risk- and recoverability-aware replanning

The first controlled research layer compared four cost structures under matched planning conditions:

| Variant | Objective |
|---|---|
| J0 | shortest path |
| J1 | path length + traversal risk |
| J2 | path length + structural recoverability penalty |
| J3 | path length + risk + recoverability penalty |

The original recoverability term was intentionally simple and structural. It was useful for building the experimental framework, but it was **not** treated as a calibrated probability of successful recovery.

That early layer established several pieces that remain useful today:

- deterministic grid planning and replanning;
- dynamic route invalidation;
- risk-aware path scoring;
- operational definitions of mission success and recovery feasibility;
- paired multi-seed evaluation;
- retained artifacts and reproducible experiment runners;
- failure taxonomies and falsification cases.

The historical J0–J3 protocol is preserved in [`docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md`](docs/archive/EXPERIMENT_PROTOCOL_V2_J0J3.md). It is research history, not the current paper claim.

### 2. We replaced vague “recoverability” with an explicit future-connectivity question

The project then moved from local structural heuristics to a sharper model: some currently free cells may close in the future, and the relevant question is whether the robot can still reach a designated safe region.

The exact reference model is implemented in:

- [`dynnav/recoverability_belief.py`](dynnav/recoverability_belief.py)
- [`dynnav/recoverability_estimation.py`](dynnav/recoverability_estimation.py)
- [`dynnav/recoverability_cut.py`](dynnav/recoverability_cut.py)

The exact oracle enumerates future closure realizations for a bounded number of hazard cells and computes safe-return probability under the current hazard belief.

We also implemented faster approximations:

- most-reliable single return path;
- two hazard-disjoint return paths;
- critical-return-cut estimate.

The approximations are not presented as exact. The repository contains explicit tests and counterexamples that show when they are conservative, tied, or optimistic.

### 3. We introduced action-triggered topology hazards

The central research mechanism is implemented in [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py).

A hazard is no longer just “this cell may become blocked.” It can be activated by a **directed robot transition**:

```text
(source cell -> target cell) activates future closure of another cell
```

This creates a key distinction:

- two trajectories can end at the same geometric cell;
- one trajectory may have activated a closure hazard;
- the other may not have activated it;
- therefore their future return-connectivity can differ.

This is the mechanism behind the current paper title:

> **When the Same Place Is Not the Same State**

The correct planning state is therefore not only `cell`; it is:

```text
(cell, activated hazard history)
```

### 4. We proved the same-state / different-history information gap constructively

The repository contains a controlled counterfactual construction where two histories reach the same final grid cell but have different exact safe-return probabilities.

In the simplest case:

- the risky history traverses a trigger;
- the safe history reaches the same geometric state without traversing it;
- the state-only marginal model assigns the same future risk to both histories;
- the history-conditioned model distinguishes them.

The corresponding experiment lives in:

[`dynnav/experiments/history_information_gap_benchmark.py`](dynnav/experiments/history_information_gap_benchmark.py)

A basic lower-bound observation used in the project is that if two histories reaching the same state have true return probabilities `R1` and `R2`, then any single state-only prediction `g(x)` must have worst-case absolute error at least `|R1 - R2| / 2` on that pair.

This is a representational argument, not a claim that history-aware planning is universally superior in every navigation problem.

### 5. We built an exact history-aware planner

The exact reference planner is:

[`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py)

Its search state is:

```text
(GridCell, frozenset[activated closure indices])
```

The planner evaluates future return probability conditioned on the hazard history that would result from each candidate transition.

The soft objective augments nominal transition cost with a recoverability term based on:

```text
1 - P(safe return | next state, activated history)
```

We also implemented:

- [`dynnav/planners/commitment_cut_astar.py`](dynnav/planners/commitment_cut_astar.py) — critical-cut approximation;
- [`dynnav/planners/commitment_safe_return_astar.py`](dynnav/planners/commitment_safe_return_astar.py) — hard safe-return constraint baseline;
- shortest/state-only baselines for controlled comparisons.

### 6. We tested the mechanism in controlled stochastic execution

The multi-commitment benchmark creates repeated situations where the short local move activates a future return-path closure hazard, while a small detour avoids activation.

Key experiment code includes:

- [`dynnav/experiments/multi_commitment_benchmark.py`](dynnav/experiments/multi_commitment_benchmark.py)
- [`dynnav/experiments/commitment_execution_benchmark.py`](dynnav/experiments/commitment_execution_benchmark.py)
- [`dynnav/experiments/commitment_phase_benchmark.py`](dynnav/experiments/commitment_phase_benchmark.py)

For stochastic execution we use **common random numbers**: the latent closure realization is sampled once per repetition/hazard and reused across planners. A planner that avoids the trigger still has the same latent draw; the event simply never becomes active.

One retained controlled result at closure probability `p = 0.8` is:

| Planner family | Irreversible/recovery-infeasible failure |
|---|---:|
| shortest / state-only | 0.992 |
| exact history-aware | 0.000 |

This is mechanism evidence in a constructed family, not a real-world performance guarantee.

### 7. We ran held-out horizon/probability tests

To test whether the behavior was limited to one small module count, we froze larger repeated-module scenarios before evaluation.

For 6 / 7 / 8 modules with 500 paired CRN seeds each, retained results include:

| Scenario | State-only / shortest | Exact history-aware |
|---|---:|---:|
| 6 modules | 0.992 failure | 0.000 |
| 7 modules | 0.998 failure | 0.000 |
| 8 modules | 1.000 failure | 0.000 |

These results support probability/horizon generalization **within the repeated-module mechanism family**. They do not establish arbitrary-map generalization.

### 8. We added geometric held-out worlds

To avoid relying only on repeated modules, we created three hand-authored frozen topologies with different geometry:

- `fork`
- `l_room`
- `chamber_two_trigger`

Each used 500 paired seeds.

Retained results:

| World | State-only / shortest failure | Exact history-aware failure | Path-length behavior |
|---|---:|---:|---|
| Fork | 0.810 | 0.000 | history planner takes the longer safe branch |
| L-room | 0.756 | 0.000 | history planner avoids the trigger without longer final path |
| Chamber | 0.890 | 0.000 | history planner takes the safe detour |

The corresponding implementation/evidence lives under the geometric-heldout experiment code and retained `results/` artifacts.

These are still constructed worlds. The repository explicitly avoids calling them “realistic general navigation benchmarks.”

### 9. We compared soft history penalties against hard safe-return constraints

A major negative result is important to the project:

**the soft history-aware objective does not universally dominate a hard safe-return constraint.**

In the three geometric worlds, hard safe-return thresholds also selected zero-hazard routes. In several cases they did so with lower single-run planning latency than the soft exact objective.

That changed the research claim. The current supported contribution is about **history-conditioned state representation and action-triggered return-connectivity**, not about proving one particular soft objective is always better.

The Pareto sweep tests multiple recoverability weights and hard thresholds and is retained as part of the evidence stack.

### 10. We built adversarial counterexamples for our own approximations

The repository includes a joint-cut adversarial world with two parallel return corridors.

Neither closure is individually critical, so the single-critical-cut approximation estimates perfect return probability. But if both closures occur, safe return is impossible.

For closure probabilities `p = 0.2, 0.5, 0.8`, the true exact return probability is:

```text
1 - p^2 = 0.96, 0.75, 0.36
```

while the critical-cut approximation remains optimistic.

Across the tested weight/probability combinations, route-history disagreement occurred in all tested settings.

This counterexample is intentionally retained because a research repository should show where its approximation fails, not only where it works.

### 11. We added statistical and measurement infrastructure

The evaluation layer contains utilities for:

- paired common-random-number comparisons;
- exact McNemar tests for paired binary outcomes;
- paired bootstrap confidence intervals;
- equivalence/non-inferiority style checks where appropriate;
- operational mission/recovery/failure labels;
- path length, latency, replanning and risk measurements;
- deterministic seed policies;
- artifact manifests and provenance.

The repository uses paired denominators wherever planners share the same generated world/event realization rather than treating all trial rows as independent.

### 12. We built a C++ ROS 2 Jazzy / Nav2 implementation

The publication-facing algorithm was then transferred from the Python reference implementation into ROS 2/Nav2.

Canonical package:

[`ros2_ws/src/dynnav_nav2_cpp`](ros2_ws/src/dynnav_nav2_cpp)

The C++ core includes:

- augmented `(costmap cell, activated-hazard bitmask)` search state;
- exact small-hazard return-connectivity enumeration;
- `initial_active_mask` support for replanning after earlier triggers;
- soft history-aware transition cost;
- proactive trigger avoidance tests;
- same-cell/different-history reliability tests;
- retained-history online replan tests.

The actual Nav2 plugin implements `nav2_core::GlobalPlanner` and exposes history-aware parameters while keeping the same plugin implementation available in shortest/history modes for controlled comparisons.

### 13. We enforced executed-history semantics in Nav2

A critical semantic rule is:

> **planned paths never activate hazards.**

Persistent hazard state changes only when the robot actually executes the configured transition.

The C++ plugin subscribes to:

```text
dynnav/executed_transition
```

and consumes transitions encoded as:

```text
sx:sy>tx:ty
```

This avoids a common modeling error where merely planning through a trigger would incorrectly alter future environment state.

### 14. We built a ROS/Gazebo benchmark layer

The benchmark package is:

[`ros2_ws/src/dynnav_nav2_benchmark`](ros2_ws/src/dynnav_nav2_benchmark)

The existing benchmark infrastructure supports:

- real Gazebo blocker spawn/move through `ros_gz_interfaces`;
- Nav2 `BasicNavigator` execution;
- planner-path subscriptions;
- global-costmap snapshots;
- blocker-observation validation;
- independent recovery-reachability checks;
- operational irreversible-failure labels;
- trial validity/exclusion reasons;
- retained traces, paths, snapshots and hashes;
- balanced planner ordering.

The older dynamic benchmark is time-triggered and is preserved separately.

### 15. We froze an action-triggered Gazebo protocol before comparative outcomes

The first action-triggered scenario is defined in:

[`ros2_ws/src/dynnav_nav2_benchmark/config/sandbox_history_triggered_events.yaml`](ros2_ws/src/dynnav_nav2_benchmark/config/sandbox_history_triggered_events.yaml)

The frozen first trigger is:

```text
(174,189) -> (175,189)
```

with closure cell:

```text
(181,191)
```

and declared closure probability:

```text
p = 0.8
```

The protocol is documented in:

[`ros2_ws/src/dynnav_nav2_benchmark/ACTION_TRIGGER_PROTOCOL.md`](ros2_ws/src/dynnav_nav2_benchmark/ACTION_TRIGGER_PROTOCOL.md)

Important rules include:

- trigger credit only from observed consecutive robot states that quantize to the configured directed adjacent cells;
- same-cell samples are ignored;
- sampling gaps are reported as observation gaps and are never interpolated;
- the latent closure draw is paired across planners;
- the physical blocker moves only if the trigger is actually observed and the paired latent closure realizes;
- trigger avoidance is a meaningful planner outcome, not an invalid trial;
- planned geometry never activates the hazard.

### 16. We wrote a current publication protocol (V3)

The current experiment contract is:

[`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md)

It defines:

- history semantics;
- paired stochastic-event rules;
- validity/exclusion rules;
- primary and secondary outcomes;
- timing/measurement requirements;
- artifact/provenance requirements;
- statistical discipline;
- limits on claims.

The old V2 filename remains only as a compatibility pointer to the archived protocol.

### 17. We built a paper and evidence-provenance pipeline

The current manuscript is:

[`paper/dynnav_r/main.tex`](paper/dynnav_r/main.tex)

**Title:**

> **When the Same Place Is Not the Same State: History-Conditioned Safe-Return Planning under Action-Triggered Topology Hazards**

The paper deliberately narrows the contribution to:

- action-triggered degradation of return-connectivity;
- same-state/different-history aliasing;
- exact augmented-state planning;
- critical-cut approximation;
- explicit approximation counterexample;
- held-out stochastic/geometric evaluation;
- ROS 2/Nav2 integration;
- carefully bounded claims.

Machine-readable evidence provenance lives in:

[`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json)

The manuscript and evidence are CI-checked so paper-facing numerical claims are tied to retained artifacts rather than copied manually without provenance.

### 18. We created an explicit claim-evidence matrix

[`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) separates:

- supported claims;
- partial claims;
- unsupported claims;
- evidence sources;
- limitations.

This is intentional. The goal is to make it difficult for implementation progress to silently become an empirical claim.

### 19. We created a falsification suite instead of only success demos

[`FAILURE_CASES.md`](FAILURE_CASES.md) includes tests designed to break or limit the approach, including:

- same-state/same-history controls;
- same-state/different-history separation;
- reverse-direction trigger controls;
- trigger sampling gaps;
- event-not-realized cases;
- false conservatism;
- hard-constraint equivalence cases;
- critical-cut joint-failure cases;
- probability miscalibration;
- correlated closures;
- delayed hazard revelation;
- kinodynamic mismatch;
- geometric generalization limits.

Negative results are retained rather than removed when they weaken the preferred method.

### 20. We hardened the repository itself

A large part of the work was research engineering rather than algorithm code.

The repository now includes:

- Python 3.10 / 3.11 / 3.12 CI;
- Ruff linting and typing checks;
- full regression tests;
- reproducibility and benchmark smoke tests;
- ROS 2 Jazzy/Nav2 plugin build and tests;
- Markdown/documentation integrity audits;
- web/research workspace builds;
- paper build/provenance checks;
- retained experiment artifacts;
- repository status and release metadata;
- citation metadata;
- explicit research archive;
- canonical repository guide.

We also cleaned stale repository metadata, removed an orphan gitlink that generated checkout warnings, fixed repository-owned Python deprecation warnings, updated publication/reproducibility documents, and closed stale PRs that were already superseded by the current `main` history.

---

## Current implementation stack

| Layer | Implementation |
|---|---|
| Planning | shortest, risk-aware, exact history-aware, critical-cut and hard safe-return planners |
| Hazard model | directed action-triggered stochastic topology closures |
| Recoverability | exact future-closure oracle plus online approximations |
| Evaluation | paired CRN trials, bootstrap intervals, McNemar/TOST utilities |
| ROS 2 / Nav2 | C++17 `nav2_core::GlobalPlanner` with persistent executed-history state |
| Gazebo | static, time-triggered dynamic and frozen action-triggered protocols |
| Publication | IEEE manuscript + machine-readable evidence manifest |
| Reproducibility | CI, frozen configs, manifests, hashes, research contracts |
| Interfaces | Streamlit lab plus FastAPI / Next.js research workspace |

---

## Retained evidence snapshot

| Study | State-only / shortest | History-conditioned | Scope |
|---|---:|---:|---|
| 3-module execution, `p=0.8` | 0.992 failure | 0 failure | controlled mechanism |
| Held-out 6/7/8 modules | 0.992 / 0.998 / 1.000 | 0 / 0 / 0 | probability/horizon generalization |
| Fork / L-room / chamber | 0.810 / 0.756 / 0.890 | 0 / 0 / 0 | three frozen hand-authored topologies |
| Joint-cut counterexample | — | approximation disagrees with exact in 9/9 tested settings | explicit failure boundary |

The geometric Pareto study showed that hard safe-return constraints can match the safe route in these worlds. The supported result is therefore about the **history-conditioned representation**, not universal superiority of the soft objective.

Authoritative paper-facing values and provenance live in [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json).

---

## What this repository does **not** claim

DynNav does **not** currently establish:

- formal safety guarantees;
- universal planner superiority;
- calibrated real-world closure probabilities;
- arbitrary-map generalization;
- collision-avoidance or kinodynamic completeness of the grid model;
- physical-robot efficacy;
- hardware reliability;
- that the critical-cut approximation is exact;
- that the soft objective dominates hard safe-return constraints.

The strongest current evidence is controlled synthetic/geometric simulation plus software/ROS integration evidence.

---

## Reviewer path

For a fast technical review, read in this order:

1. [`paper/dynnav_r/main.tex`](paper/dynnav_r/main.tex) — scientific argument and results.
2. [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) — artifact/run provenance.
3. [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) — supported vs unsupported claims.
4. [`EXPERIMENT_PROTOCOL_V3.md`](EXPERIMENT_PROTOCOL_V3.md) — current experiment semantics.
5. [`FAILURE_CASES.md`](FAILURE_CASES.md) — falsification and negative cases.
6. [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py) — action-trigger model.
7. [`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py) — exact planner.
8. [`ros2_ws/src/dynnav_nav2_cpp`](ros2_ws/src/dynnav_nav2_cpp) — C++ Nav2 implementation.
9. [`ros2_ws/src/dynnav_nav2_benchmark`](ros2_ws/src/dynnav_nav2_benchmark) — ROS/Gazebo benchmark.
10. [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) — canonical code/evidence map.

---

## Canonical repository map

```text
dynnav/                             Python research core
  planners/                         exact/approximate/baseline planners
  experiments/                      controlled and held-out studies
  evaluation/                       statistics and outcome metrics

ros2_ws/src/dynnav_nav2_cpp/        C++ Nav2 history-aware planner
ros2_ws/src/dynnav_nav2_benchmark/  ROS/Gazebo validation infrastructure
paper/dynnav_r/                      IEEE paper + evidence manifest
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

Older top-level modules remain for compatibility and historical experiments. They are not automatically part of the publication-facing evidence path.

---

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

---

## Research discipline

A publication-facing claim in DynNav is expected to have:

- an implemented mechanism;
- deterministic regression coverage;
- frozen configuration and seed policy;
- retained machine-readable output;
- provenance to source revision/configuration;
- appropriate paired/statistical analysis;
- at least one explicit limitation or failure boundary.

The next major evidence jump is retained action-triggered Gazebo execution under the frozen V3 semantics, followed by partial-observability, delayed-revelation, miscalibration and correlation stress tests if the execution evidence is valid.

---

## Policies and supporting documents

[Repository guide](docs/REPOSITORY_GUIDE.md) · [Claims](CLAIM_EVIDENCE_MATRIX.md) · [Current protocol](EXPERIMENT_PROTOCOL_V3.md) · [Failure cases](FAILURE_CASES.md) · [Research archive](docs/archive/README.md) · [Contributing](CONTRIBUTING.md) · [Citation](CITATION.cff) · [Security](SECURITY.md) · [License](LICENSE)
