# System Architecture

DynNav is structured as a layered research stack.

```text
configs/                 experiment and benchmark YAML files
src/dynnav/              reusable Python research package
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
