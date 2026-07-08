# Contributing

Thank you for improving DynNav. Contributions should preserve the repository's scientific standard: implemented behavior must be distinguishable from prototypes and future work.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pre-commit install
```

## Quality checks

Before opening a pull request, run:

```bash
ruff check src tests scripts
black --check src tests scripts
pytest
```

## Research claims

Do not describe a component as validated unless the repository contains:

1. the implementation;
2. a deterministic benchmark or test;
3. the configuration and seed range;
4. raw outputs or generated summaries;
5. limitations and failure cases.

## Pull requests

Use small, reviewable changes. Include motivation, implementation notes, tests, and known limitations.
