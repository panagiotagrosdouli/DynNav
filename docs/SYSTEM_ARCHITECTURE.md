# System Architecture

**Current correction (2026-11-09):** The authoritative Python research package is `dynnav/` (verified by the CI canonical package assertion), not `src/dynnav/`. The following layered overview describes the historical research design; use [Repository Guide](REPOSITORY_GUIDE.md) and [Full Repository Topology](FULL_REPOSITORY_TOPOLOGY_2026-11-09.md) for current paths and execution boundaries.

DynNav is structured as a layered research stack.

```text
configs/                 experiment and benchmark YAML files
dynnav/                  canonical Python research package
scripts/                 command-line experiment, figure, and demo tools
tests/                   pytest regression and smoke tests
docs/                    scientific and engineering documentation
paper/                   paper-facing text fragments
website/                 research website scaffold
assets/                  generated static media
results/                 generated metrics, plots, tables, and videos
```

## Runtime layers

1. **Scenario layer** creates deterministic occupancy, uncertainty, and dynamic-obstacle conditions.
2. **Belief layer** stores occupancy probabilities and propagated uncertainty fields.
3. **Risk layer** converts occupancy and uncertainty into bounded cell and trajectory risk.
4. **Planning layer** selects a nominal or conservative policy and plans a trajectory.
5. **Rerouting layer** triggers replanning when risk, blockage, or recoverability thresholds are violated.
6. **Supervision layer** emits nominal, cautious, replan, safe-mode, or safe-stop decisions.
7. **Evaluation layer** writes CSV/JSON summaries and generated figures.

## Key APIs

- `dynnav.core`: typed maps, poses, trajectories, path-evaluation records, and self-awareness utilities.
- `dynnav.planning`: risk-aware A*, dynamic rerouting, recoverability estimator, and planner switching.
- `dynnav.research_modules`: integrated uncertainty propagation, mission-risk estimation, runtime monitoring, and safe-mode supervision.
- `dynnav.benchmarks`: deterministic benchmark execution and result serialization.

## Design principles

- Keep algorithms independent of ROS2 so they can run in CI.
- Keep ROS2 as an adapter layer rather than a hidden dependency.
- Prefer deterministic seeds for every benchmark.
- Record limitations near the claim they qualify.
- Expose typed APIs for planners, monitors, supervisors, and experiment runners.

## Limitation

The architecture is suitable for reproducible synthetic experiments and portfolio evaluation. Hardware validation, timing guarantees, and formal proofs remain future work unless supported by new logs and verification artifacts.

## Current integration boundaries (2026-11-09)

- **Research core:** `dynnav/` is the canonical package. `dynnav/commitment_hazard.py`, `dynnav/recoverability_belief.py` and `dynnav/planners/` implement the publication-facing hazard/history and planning models; `dynnav/experiments/` and `scripts/` run experiments.
- **ROS 2/Nav2:** `ros2_ws/src/dynnav_nav2_cpp/` is the Jazzy C++ planner and `ros2_ws/src/dynnav_nav2_benchmark/` provides integration benchmarks. Passing CI demonstrates the stated build/test contracts, not physical-robot efficacy.
- **Contributions:** `contributions/` contains the C01–C26 registered smoke-experiment tracks, C27 theory outside that registry, and shared historical modules. Consult `configs/contributions/registry.yaml` and `experiments.yaml`.
- **Research API:** `apps/api/main.py` is a thin ASGI import of `dynnav.researcher.api`. The service has real FastAPI endpoints, but it must be running for the Researcher frontend to execute server-side experiments.
- **Web surfaces:** `website/` is the public portal, `apps/web/` is the Researcher Next.js frontend (development API URL defaults to localhost), `vercel_app/` is a separately built frontend, and `app/` is Streamlit. `scripts/build_web_portal.sh` combines the first two for static Pages hosting; static hosting does not run the Python API.
- **Evidence:** `paper/dynnav_r/evidence_manifest.json`, `CLAIM_EVIDENCE_MATRIX.md` and `PUBLICATION_READINESS.md` define publication claim boundaries. LILocBench descriptive trajectory results must not be treated as planner comparison or hardware validation.
- **Historical compatibility:** Do not remove or relocate `core/`, `modules/`, `nav_research/`, split C07, `test/` or legacy logs without import/call-site audits, regression testing, metric equivalence and provenance checks.

This note corrects current paths without deleting the original conceptual runtime-layer description.
