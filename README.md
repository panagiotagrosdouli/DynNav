# DynNav: Risk-Aware Dynamic Navigation in Unknown Environments

[![CI](https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/actions/workflows/ci.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)](pyproject.toml)

DynNav is a research-grade software scaffold for studying **risk-aware dynamic navigation and rerouting in unknown or partially observed environments**. It focuses on scientifically honest, reproducible prototypes: occupancy-belief grids, A*/Dijkstra baselines, risk-aware planning, uncertainty fields, recoverability estimation, runtime safety supervision, deterministic benchmarks, automated figures, and ROS2/Nav2 integration scaffolds.

**Author:** Panagiota Grosdouli, Department of Electrical & Computer Engineering, Democritus University of Thrace

## Central research question

> How can an autonomous robot dynamically reroute in unknown and changing environments while reasoning about uncertainty, risk, recoverability, and mission safety?

DynNav treats path length as only one part of the navigation objective. In unknown dynamic environments, a geometrically short route can be unsafe if it passes through uncertain cells, near moving obstacles, or into states with poor escape routes.

## Scientific identity

DynNav studies:

- autonomous navigation in unknown environments;
- dynamic rerouting and online replanning;
- risk-aware and uncertainty-aware planning;
- recoverability-aware autonomy;
- mission-level safety supervision;
- learning-augmented planning interfaces;
- ROS2/Nav2 integration as a transparent prototype path.

## Scope and maturity

This repository is a research prototype, not a certified robotic safety system. Components are labeled conservatively:

- **Implemented:** code exists, has tests or smoke workflows, and can run in the default Python environment.
- **Prototype:** code or documentation exists, but validation is incomplete or depends on optional middleware.
- **Planned:** documented research direction without completed implementation.

| Component | Status | Evidence |
|---|---|---|
| Typed grid, pose, trajectory, and mission-state primitives | Implemented | `src/dynnav/core.py`, tests |
| A* and Dijkstra baselines | Implemented | `src/dynnav/lab_grade.py`, `tests/test_lab_grade.py` |
| Risk-aware A* planning | Implemented | `src/dynnav/planning.py`, tests |
| Risk, uncertainty, and recoverability fields | Implemented | deterministic NumPy implementation + tests |
| Dynamic rerouting trigger and cooldown | Prototype | threshold supervisor + tests |
| Runtime safety supervisor | Prototype | explicit safe-stop / safe-mode / replan policy |
| Reproducible research-suite manifest | Implemented | `configs/research_suite.yaml` |
| CSV/JSON research-suite runner | Prototype | `scripts/run_research_suite.py` |
| Visualization and demo-generation scripts | Implemented | script-level outputs, no fabricated metrics |
| ROS 2 / Nav2 integration | Prototype | docs/scaffold only; no compiled plugin claim |
| Formal safety guarantees and hardware validation | Planned | requires future proofs, logs, and experiments |

## Problem formulation

DynNav represents the robot state `x_t`, occupancy belief `b_t`, local costmap `C_t`, dynamic obstacles `O_t`, uncertainty field `U_t`, risk field `R_t`, and recoverability field `Γ_t`. A navigation policy chooses a path `π_t` that balances path length, risk exposure, uncertainty exposure, and loss of recoverability. Rerouting is triggered when a path is blocked or when risk, uncertainty, or recoverability cross mission thresholds.

See [`docs/MATHEMATICAL_FORMULATION.md`](docs/MATHEMATICAL_FORMULATION.md) for the full notation and objective.

## System architecture

```text
configs/          YAML experiment definitions
src/dynnav/       reusable Python research package
scripts/          benchmark, figure, and demo-generation entry points
tests/            pytest suite
.github/          CI workflows
docs/             scientific and engineering documentation
paper/            paper-facing text fragments
website/          Next.js + TypeScript + Tailwind research site scaffold
assets/           generated diagrams and demo GIFs
results/          generated benchmark CSVs, summaries, figures, videos
```

Runtime flow:

```text
Scenario / perception -> occupancy belief -> uncertainty propagation
        -> risk and recoverability fields -> planner registry
        -> risk-aware planner -> rerouting supervisor
        -> safety supervisor -> benchmark logs and figures
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Docker:

```bash
docker build -t dynnav .
docker run --rm dynnav
```

## Quick start

Run the Python test suite:

```bash
pytest
```

Run the deterministic research-suite smoke runner:

```bash
python scripts/run_research_suite.py --out-dir results/research_suite
```

Run the existing benchmark entry point:

```bash
dynnav-benchmark \
  --config configs/benchmark.yaml \
  --out-csv results/benchmarks/dynnav_benchmark.csv \
  --summary results/benchmarks/summary.md
```

The benchmark uses deterministic seeds and keeps failed planning episodes in the CSV output. Generated numbers should be reported only after the exact config, seed, and output files are committed.

## Generate research assets

```bash
python scripts/generate_research_assets.py
python scripts/make_demo_gif.py
```

Expected outputs include architecture diagrams, navigation pipeline diagrams, risk heatmaps, trajectory plots, uncertainty plots, `assets/demo.gif`, and `results/videos/demo.mp4` when local codecs are available. If an output is missing, it should be marked Pending rather than described as a result.

## Evaluation metrics

DynNav tracks path length, planning time, expanded nodes, success, collision proxy, near-miss proxy, reroute count, risk exposure, uncertainty exposure, terminal recoverability, and mission safety mode. The metrics are defined for reproducible comparison, not for unsupported state-of-the-art claims.

## Documentation map

- `docs/REPOSITORY_AUDIT.md` — scientific, engineering, reproducibility, and presentation audit.
- `docs/RESEARCH_OVERVIEW.md` — research scope, motivation, and limitations.
- `docs/MATHEMATICAL_FORMULATION.md` — formal notation, risk objective, rerouting rule, and safety supervisor.
- `docs/SYSTEM_ARCHITECTURE.md` — repository and runtime architecture.
- `docs/NAVIGATION_PIPELINE.md` — closed-loop pipeline.
- `docs/UNCERTAINTY_MODEL.md` — belief-grid uncertainty model.
- `docs/RISK_ESTIMATION.md` — mission-risk and CVaR-style summaries.
- `docs/ROS2_NAV2_INTEGRATION.md` — honest ROS2/Nav2 prototype interface.
- `docs/EVALUATION_PROTOCOL.md` — benchmark reporting protocol.
- `docs/REPRODUCIBILITY.md` — environment and deterministic execution.
- `docs/ROADMAP.md` — staged future work.

## ROS2/Nav2 usage

ROS2/Nav2 integration is currently **Prototype**. The intended integration path is a Nav2 global planner plugin that consumes occupancy grids, publishes risk/uncertainty/recoverability debug grids, and exposes safety-mode events to a behavior tree. See [`docs/ROS2_NAV2_INTEGRATION.md`](docs/ROS2_NAV2_INTEGRATION.md).

## Limitations

- The current implementation is grid-world oriented.
- Dynamic obstacle handling is a deterministic prototype.
- ROS2/Nav2 support is not yet a compiled plugin.
- No hardware validation, Gazebo validation, or formal safety guarantee is claimed.
- No benchmark numbers should be quoted unless generated by scripts and traceable to committed configs.

## Future PhD directions

1. Belief-space planning with learned uncertainty calibration.
2. Recoverability-aware model predictive control.
3. Risk-sensitive dynamic obstacle prediction.
4. Formal analysis of rerouting stability and safe-mode switching.
5. Hardware experiments with ROS2/Nav2 and logged reproducibility artifacts.

## Website

A Next.js, TypeScript, TailwindCSS, and Framer Motion research-site scaffold is provided under `website/`.

```bash
cd website
npm install
npm run dev
```

## Citation

See `CITATION.cff` and `paper/` for citation and manuscript-facing text fragments.

## License

Apache License, Version 2.0. See `LICENSE`.
