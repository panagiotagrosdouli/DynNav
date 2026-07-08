# Release Notes

## 0.1.0 — Research scaffold

This release establishes DynNav as a reproducible research-software scaffold.

### Added

- Python package under `src/dynnav`.
- Typed primitives for grid maps, poses, and trajectories.
- Risk-aware A* planner with recoverability and returnability terms.
- Dynamic rerouting and planner-switching abstractions.
- Runtime monitor and safe-mode supervisor.
- Deterministic synthetic scenario generator.
- YAML configuration system.
- Benchmark runner with CSV and Markdown outputs.
- Figure and demo-generation scripts.
- Next.js research website scaffold.
- CI, Docker, pre-commit hooks, tests, citation metadata, contribution guide, security policy, and code of conduct.

### Limitations

- The default package uses grid-world prototypes.
- ROS 2 and hardware validation remain experimental or planned.
- Formal safety claims require future proofs and validation logs.
