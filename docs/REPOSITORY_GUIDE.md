# DynNav Repository Guide

This guide separates the **canonical publication path** from engineering support, exploratory modules, retained artifacts, and historical compatibility code. It exists so a reviewer can understand the repository without assuming that every directory is equally mature or equally relevant to the central research claim.

## 1. Canonical publication path

These are the files and directories that directly support the current history-conditioned safe-return paper.

| Area | Canonical path | Role |
|---|---|---|
| Hazard model | `dynnav/commitment_hazard.py` | action-triggered stochastic closure model and history semantics |
| Exact recoverability | `dynnav/recoverability_belief.py` | exact future-closure safe-return probability oracle |
| Approximation | `dynnav/recoverability_cut.py` | critical-return-cut estimator and documented approximation boundary |
| Exact planner | `dynnav/planners/commitment_aware_astar.py` | augmented-state history-aware planner |
| Cut planner | `dynnav/planners/commitment_cut_astar.py` | scalable critical-cut approximation |
| Hard baseline | `dynnav/planners/commitment_safe_return_astar.py` | probability-threshold safe-return baseline |
| State-only baseline | `dynnav/planners/hazard_reliability_astar.py` | state-only marginal return-risk comparison |
| Experiments | `dynnav/experiments/` | mechanism, execution, scaling, held-out and adversarial studies |
| Statistical support | `dynnav/experiments/statistics.py` | paired bootstrap / McNemar / TOST utilities |
| Runners | `scripts/run_*` | retained, scriptable experiment entry points |
| Paper | `paper/dynnav_r/` | IEEE manuscript, bibliography, protocols and evidence manifest |
| Nav2 planner | `ros2_ws/src/dynnav_nav2_cpp/` | C++ ROS 2 Jazzy / Nav2 global planner |
| ROS/Gazebo validation | `ros2_ws/src/dynnav_nav2_benchmark/` | benchmark scenarios, launch support and execution contracts |
| Regression tests | `tests/` and ROS package tests | implementation and research-contract checks |

## 2. Evidence hierarchy

DynNav deliberately distinguishes code existence from evidence maturity.

### Level A — implementation evidence

Unit tests, deterministic known-answer cases, parser/configuration checks and build/discovery checks establish that an implementation behaves according to its local contract. They do not establish an efficacy claim.

### Level B — controlled mechanism evidence

Synthetic commitment traps, analytic phase-boundary tests and same-state/different-history examples isolate the mechanism. These support understanding of why a planner behaves differently, not general deployment claims.

### Level C — retained comparative evidence

Paired common-random-number stochastic experiments, held-out module families, frozen geometric topologies and adversarial counterexamples are retained as machine-readable artifacts and linked in `paper/dynnav_r/evidence_manifest.json`.

### Level D — ROS2/Nav2 integration evidence

The C++ planner builds, loads and passes Nav2 integration checks. Persistent activated-hazard state is updated from executed-transition input rather than from a planned path.

### Level E — execution-level validation

The action-triggered Gazebo protocol is frozen, but new history-conditioned execution efficacy numbers should only be promoted after valid retained runs satisfy trigger-observation, blocker-injection, costmap-observation and recovery-label contracts.

### Not currently claimed

Physical-robot efficacy, safety certification, universal superiority and broad real-world generalization are outside the current evidence boundary.

## 3. Retained evidence and provenance

The authoritative publication-facing provenance file is:

`paper/dynnav_r/evidence_manifest.json`

Use it before quoting a numerical result. It records the retained workflow/artifact source for the values used by the manuscript.

Important experiment families include:

- history information gap;
- analytic commitment phase boundary;
- stochastic commitment execution;
- critical-cut scaling;
- held-out probability/horizon generalization;
- joint-cut adversarial counterexample;
- geometric held-out topologies;
- soft-history vs hard-safe-return Pareto sweep.

`CLAIM_EVIDENCE_MATRIX.md` summarizes which claims are supported, partial, or intentionally unsupported.

## 4. Canonical engineering paths

| Purpose | Path |
|---|---|
| Python package | `dynnav/` |
| Python tests | `tests/` |
| Research scripts | `scripts/` |
| Experiment config | `configs/` |
| Retained outputs | `results/` |
| ROS 2 workspace | `ros2_ws/src/` |
| Streamlit lab | `app/` |
| FastAPI service | `apps/api/` |
| Next.js workspace | `apps/web/` |
| Documentation | `docs/` |
| Paper | `paper/dynnav_r/` |

New publication-facing work should prefer these locations unless a package boundary requires otherwise.

## 5. Exploratory and historical areas

The repository grew through multiple research phases. Several top-level directories contain older prototypes, side investigations, compatibility code or exploratory contributions. Their presence is useful for research history, but it does **not** imply equal validation maturity.

Examples include `contributions/`, `research_experiments/`, `nav_research/`, `neural_uncertainty/`, `cybersecurity_ros2/`, `photogrammetry_module/`, `ig_explorer/`, older `core/` / `modules/` helpers, and legacy log directories.

Rules for interpreting these areas:

1. do not treat them as evidence for the current paper unless the evidence manifest explicitly references them;
2. do not promote a prototype to the README as a validated contribution without a frozen experiment and retained artifact;
3. prefer deprecation/documentation over disruptive moves when a directory may still be imported by legacy experiments;
4. move new research into the canonical package/workspace structure where possible.

## 6. Reviewer workflow

A fast research review can be done in this order:

1. `README.md` — research question and evidence snapshot;
2. `paper/dynnav_r/main.tex` — full scientific argument;
3. `paper/dynnav_r/evidence_manifest.json` — provenance;
4. `CLAIM_EVIDENCE_MATRIX.md` — claim boundary;
5. `dynnav/commitment_hazard.py` — problem semantics;
6. `dynnav/planners/commitment_aware_astar.py` — reference planner;
7. `dynnav/experiments/` — frozen evaluations;
8. `ros2_ws/src/dynnav_nav2_cpp/` — deployment-oriented implementation;
9. `ros2_ws/src/dynnav_nav2_benchmark/` — execution validation infrastructure.

## 7. Contribution standard

A new central-research contribution should normally provide:

- implementation;
- deterministic regression contract;
- frozen configuration and seeds;
- baseline comparison;
- retained raw/machine-readable output;
- paired/statistical analysis when applicable;
- provenance in a manifest;
- failure case / limitation;
- documentation that distinguishes evidence from hypothesis.

This is the standard used to keep DynNav a research repository rather than a collection of disconnected demos.
