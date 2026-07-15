# `dynnav` Python package

This is the installable research package for deterministic grid-based navigation experiments.

**Status:** mixed maturity. Mapping and baseline planning are **Implemented** and tested. Rerouting, supervision, recoverability, and research orchestration are **Research Prototypes**. ROS2/Nav2 and Gazebo execution are not provided by this package.

## Public entry points

The package exposes the console commands configured in [`../../pyproject.toml`](../../pyproject.toml):

```bash
dynnav-benchmark --help
dynnav-demo --help
```

Important modules exercised by CI include:

- `mapping`: occupancy-grid data structures and conversions;
- `planning`: deterministic planning interfaces and baseline behavior;
- `benchmarks`: benchmark command implementation;
- `lab_grade`: typed research integration primitives;
- `research_modules`: risk, uncertainty, recoverability, and supervision prototypes;
- `research_pipeline`: deterministic orchestration and generated artifacts.

## Processing flow

```text
configuration / scenario
  -> occupancy representation
  -> risk, uncertainty, and recoverability estimates
  -> planner
  -> rerouting and mission supervision
  -> metrics and generated artifacts
```

## Tests

```bash
pytest tests/test_mapping_occupancy_grid.py
pytest tests/test_planning.py
pytest tests/test_research_modules.py
pytest tests/test_research_pipeline_phase2.py
```

## Limitations

- Grid-world evidence is not equivalent to robot or Gazebo validation.
- Dynamic-obstacle handling is not yet a validated probabilistic space-time predictor.
- Safety supervision is rule-based and provides no formal safety guarantee.
- Quantitative claims require traceable generated results and configurations.

See [`../../docs/REPOSITORY_AUDIT.md`](../../docs/REPOSITORY_AUDIT.md), [`../../docs/MATHEMATICAL_FORMULATION.md`](../../docs/MATHEMATICAL_FORMULATION.md), and the [root README](../../README.md).
