# DynNav technical documentation

This directory is the technical documentation index for the current DynNav research prototype.

DynNav investigates deterministic, grid-based navigation and rerouting under occupancy uncertainty, risk, recoverability constraints, and mission-level supervision. Documentation must be read together with executable source, tests, configurations and generated evidence. No formal safety guarantee, production Nav2 plugin, Gazebo validation, TurtleBot validation or hardware result is claimed by this index.

## Documentation map

- [`REPOSITORY_AUDIT.md`](REPOSITORY_AUDIT.md): current capabilities, evidence gaps and implementation order.
- [`MARKDOWN_AUDIT.md`](MARKDOWN_AUDIT.md): repository-wide Markdown review and remaining validation.
- [`MARKDOWN_STYLE_GUIDE.md`](MARKDOWN_STYLE_GUIDE.md): maturity vocabulary, claim discipline and link policy.
- [`RESEARCH_OVERVIEW.md`](RESEARCH_OVERVIEW.md): central research question, motivation and scope.
- [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md): current package and processing architecture.
- [`NAVIGATION_PIPELINE.md`](NAVIGATION_PIPELINE.md): observation-to-planning and supervision flow.
- [`MATHEMATICAL_FORMULATION.md`](MATHEMATICAL_FORMULATION.md): current objective, notation and assumptions.
- [`UNCERTAINTY_MODEL.md`](UNCERTAINTY_MODEL.md): uncertainty representation and known limitations.
- [`RISK_ESTIMATION.md`](RISK_ESTIMATION.md): risk terms, aggregation and evidence boundary.
- [`EVALUATION_PROTOCOL.md`](EVALUATION_PROTOCOL.md): scenarios, baselines, metrics and fair-comparison rules.
- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md): seeds, commands, configurations and artifact traceability.
- [`ROS2_NAV2_INTEGRATION.md`](ROS2_NAV2_INTEGRATION.md): prototype integration direction and unvalidated items.

## Maturity vocabulary

- **Implemented:** source exists and is exercised by tests or CI.
- **Research Prototype:** executable or scaffolded, but not deployment-ready.
- **Experimental:** evaluated only in limited or synthetic settings.
- **Planned:** no complete implementation is claimed.
- **Pending Validation:** implementation or command exists but required evidence is incomplete.
- **Simulation Only:** evidence comes from simulation and is not a hardware result.
- **Hardware Validation Required:** no physical-robot evidence is available.

## Verified commands

From the repository root:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/ci_smoke
python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/ci_benchmarks
```

The website is checked separately:

```bash
cd website
npm install --no-audit --no-fund
npm run typecheck
npm run build
```

## Documentation policy

A conceptual architecture diagram is not experimental evidence. Passing unit tests is not proof of navigation safety. Synthetic benchmarks must be labelled synthetic. Quantitative claims must link to generated results, configuration, seed and command. ROS2, Nav2, Gazebo, simulation and hardware status must be stated independently.

See the [root README](../README.md), [`configs`](../configs/README.md), [`scripts`](../scripts/README.md) and [`tests`](../tests/README.md) guides.
