# DynNav Contributions

This directory contains the numbered DynNav research contributions and supporting experimental modules.

## Documentation convention

Each numbered contribution should use the following structure where applicable:

```text
NN_module_name/
├── README.md          # Primary English overview
├── README_GR.md       # Optional Greek overview
├── code/              # Implementation, when separated from experiments
├── experiments/       # Reproducible experiment entry points
├── results/           # Generated or committed result artifacts
├── models/            # Model artifacts or model definitions
└── docs/              # Extended theory, protocols, and evidence notes
```

Only `README.md` and, optionally, `README_GR.md` should serve as module entry points. Legacy variants such as `readmegr.md` are consolidated to prevent duplication and broken navigation.

## Evidence and maturity

Documentation should distinguish clearly between:

- **Implemented**: source code and tests are present;
- **Experimental**: evidence is limited to controlled synthetic or benchmark runs;
- **Planned**: design or roadmap material exists without validated implementation;
- **Hardware validation required**: no physical-robot evidence is currently available.

Passing tests or synthetic experiments must not be described as formal safety certification or real-world validation.

## Numbered contributions

The canonical numbered modules are `01` through `27`. Supporting folders such as benchmarking, ablation studies, hybrid planners, and realtime replanning are shared research infrastructure rather than separate numbered contributions.

See the repository root [`README.md`](../README.md) and [`docs/REPOSITORY_AUDIT.md`](../docs/REPOSITORY_AUDIT.md) for the authoritative project-level status and evidence boundaries.
