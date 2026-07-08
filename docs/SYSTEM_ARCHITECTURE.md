# System Architecture

DynNav is structured as a layered research system.

```text
configs/          reproducible YAML experiment definitions
src/dynnav/       core research package
scripts/          asset and demo generation entry points
tests/            unit and smoke tests
docs/             scientific and engineering documentation
paper/            concise paper-facing text fragments
website/          research website scaffold
results/          generated benchmark outputs and figures
assets/           generated documentation figures and demo GIF
```

## Runtime layers

1. **Scenario and belief layer**: constructs occupancy-belief grids with deterministic seeds.
2. **Risk layer**: summarizes occupancy probability, uncertainty, and path risk.
3. **Planning layer**: runs risk-aware search and estimates recoverability.
4. **Rerouting layer**: replans when risk or recoverability crosses a threshold.
5. **Monitoring layer**: evaluates runtime invariants and selects nominal, slow, or stop mode.
6. **Benchmark layer**: writes CSV outputs and Markdown summaries.
7. **Visualization layer**: produces figures used in documentation and reports.

## Design rationale

The architecture keeps ROS 2-facing code separate from the deterministic Python core. This allows unit tests to run without robot middleware while preserving a path toward integration with Nav2, Gazebo, TurtleBot3, or custom mobile robot platforms.

## Expected impact

This layout improves maintainability, reproducibility, and scientific reviewability. A reader can inspect the implemented algorithmic claims independently from future hardware or middleware extensions.
