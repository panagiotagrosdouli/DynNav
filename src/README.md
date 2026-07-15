# Source tree

The installable Python code lives under [`dynnav/`](dynnav/). The optional dashboard package is also included in the wheel when present.

**Maturity:** Core Python package implemented and CI-tested; several research integrations remain prototypes.

## Package boundaries

- [`dynnav/`](dynnav/): grid navigation, mapping, planning, research metrics, benchmark entry points, and orchestration.
- `dynnav_dashboard/`: optional Streamlit-facing code when installed with `.[dashboard]`.

The wheel configuration is defined in [`../pyproject.toml`](../pyproject.toml).

## Install and import

```bash
python -m pip install -e ".[dev]"
python -c "import dynnav; print(dynnav.__file__)"
```

## Verification

```bash
pytest
ruff check src
mypy src/dynnav/mapping --strict --no-warn-unused-ignores --show-error-codes
```

Only the mapping package is currently checked with strict mypy in CI. Repository-wide type coverage is **Pending Validation**.

See the [package README](dynnav/README.md), the [architecture documentation](../docs/SYSTEM_ARCHITECTURE.md), and the [root README](../README.md).
