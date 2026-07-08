# DynNav: Risk-Aware Dynamic Navigation in Unknown Environments

[![CI](https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/actions/workflows/ci.yml/badge.svg)](https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)](pyproject.toml)

DynNav is a research-grade software scaffold for studying risk-aware dynamic navigation and rerouting in unknown or partially observed environments. It focuses on scientifically honest, reproducible prototypes: occupancy-belief grids, risk-aware planning, recoverability estimation, runtime monitoring, deterministic benchmarks, automated figures, and a research website scaffold.

**Author:** Panagiota Grosdouli, Department of Electrical & Computer Engineering, Democritus University of Thrace

## Scope and maturity

This repository is a research prototype, not a certified robotic safety system. Components are labeled conservatively:

- **Implemented:** code exists, has tests or smoke workflows, and can run in the default Python environment.
- **Experimental:** code or documentation exists, but validation is incomplete or depends on optional middleware.
- **Planned:** documented research direction without completed implementation.

| Component | Status | Default CI coverage |
|---|---|---|
| Typed grid, pose, and trajectory primitives | Implemented | Unit tests |
| Risk-aware A* planning | Implemented | Unit tests + benchmark smoke test |
| Recoverability / returnability scoring | Implemented | Planner tests |
| Dynamic rerouting trigger | Implemented | Import-level coverage |
| Runtime monitor and safe-mode supervisor | Implemented | Unit tests |
| Uncertainty propagation prototype | Implemented | Unit tests |
| Deterministic scenario generator | Implemented | Benchmark smoke test |
| CSV benchmark runner and Markdown summaries | Implemented | CI smoke test |
| Visualization and demo-generation scripts | Implemented | Manual/script execution |
| ROS 2 / Nav2 integration | Experimental | Not in default CI |
| Formal safety guarantees and hardware validation | Planned | Requires future logs/proofs |

## Scientific motivation

Navigation in unknown environments requires decisions under incomplete information. Shortest-path planners can select trajectories that are geometrically efficient but unsafe under map uncertainty, low recoverability, or delayed observations. DynNav exposes uncertainty as a first-class input to planning and supervision so that navigation behavior can be evaluated through safety-efficiency trade-offs rather than path length alone.

## Architecture

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
        -> risk-aware planner -> recoverability estimator
        -> runtime monitor -> reroute or safe-mode supervision
        -> benchmark logs and figures
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

## Reproducible benchmark

```bash
dynnav-benchmark \
  --config configs/benchmark.yaml \
  --out-csv results/benchmarks/dynnav_benchmark.csv \
  --summary results/benchmarks/summary.md
```

The benchmark uses deterministic seeds and keeps failed planning episodes in the CSV output.

## Generate research assets

```bash
python scripts/generate_research_assets.py
python scripts/make_demo_gif.py
```

Expected outputs include architecture diagrams, navigation pipeline diagrams, risk heatmaps, trajectory plots, uncertainty plots, `assets/demo.gif`, and `results/videos/demo.mp4` when local codecs are available.

## Documentation map

- `docs/RESEARCH_OVERVIEW.md` — research scope, motivation, and limitations.
- `docs/SYSTEM_ARCHITECTURE.md` — repository and runtime architecture.
- `docs/NAVIGATION_PIPELINE.md` — closed-loop pipeline.
- `docs/UNCERTAINTY_MODEL.md` — belief-grid uncertainty model.
- `docs/RISK_ESTIMATION.md` — mission-risk and CVaR-style summaries.
- `docs/EVALUATION_PROTOCOL.md` — benchmark reporting protocol.
- `docs/REPRODUCIBILITY.md` — environment and deterministic execution.
- `docs/ROADMAP.md` — staged future work.

## Software quality

The repository includes:

- `pyproject.toml` with package metadata and tool configuration;
- Black, Ruff, pytest, coverage configuration;
- GitHub Actions CI;
- pre-commit hooks;
- Dockerfile;
- typed Python modules with Google-style docstrings;
- tests for core planning, monitoring, and uncertainty utilities.

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
