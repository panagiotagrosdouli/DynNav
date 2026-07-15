# Test suite

The repository uses pytest for deterministic Python validation.

**Status:** Python tests are **Implemented** and run on Python 3.10, 3.11, and 3.12 in GitHub Actions. ROS2, Nav2, Gazebo, and hardware tests are **Pending Validation**.

## Run tests

```bash
pytest
```

Focused examples:

```bash
pytest tests/test_mapping_occupancy_grid.py
pytest tests/test_planning.py
pytest tests/test_realtime_replanning.py
pytest tests/test_research_modules.py
pytest tests/test_research_pipeline_phase2.py
```

The CI workflow currently runs selected source-package tests and then executes remaining top-level `test_*.py` files individually with a five-minute per-file timeout. See [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Test expectations

Tests should assert behavior, not merely import or execute code. New work should cover:

- deterministic outputs for fixed seeds;
- path validity and obstacle avoidance;
- risk, uncertainty, and recoverability semantics;
- bounded replanning and explicit failure reasons;
- generated manifest and artifact contracts;
- configuration rejection for invalid inputs.

## Limitations

Passing unit tests does not establish navigation safety, real-time performance, ROS integration, simulation validity, or hardware readiness. Those claims require separate evidence.

See [`../docs/EVALUATION_PROTOCOL.md`](../docs/EVALUATION_PROTOCOL.md), [`../docs/REPOSITORY_AUDIT.md`](../docs/REPOSITORY_AUDIT.md), and the [root README](../README.md).
