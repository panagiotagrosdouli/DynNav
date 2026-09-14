# Contributing to DynNav

DynNav is a research repository. Contributions should make it easier to distinguish **implemented behavior**, **retained evidence**, **exploratory work**, and **future hypotheses**.

## Canonical development areas

Prefer these locations for new central work:

- `dynnav/` — canonical Python research package;
- `tests/` — Python regression and research-contract tests;
- `scripts/` — reproducible experiment runners and audits;
- `configs/` — frozen experiment configuration;
- `results/` — retained machine-readable evidence;
- `ros2_ws/src/` — ROS 2 / Nav2 / Gazebo packages;
- `paper/dynnav_r/` — publication-facing manuscript and evidence manifest;
- `docs/` — engineering and scientific documentation.

Exploratory programmes may live elsewhere, but they must not be presented as evidence for the central paper unless the evidence manifest explicitly links them.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"
pre-commit install
```

## Required quality checks

Before opening a pull request, run the relevant subset of:

```bash
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
python -m pytest -q
```

For ROS 2 changes, also build and test the affected Jazzy packages. For paper changes, compile `paper/dynnav_r/main.tex` and preserve provenance checks. Web changes must pass the workspace type-check/build and dependency audit used by CI.

## Research evidence standard

Do not describe a component as validated merely because code or a demo exists. A publication-facing result should normally include:

1. implementation;
2. deterministic regression/known-answer test;
3. frozen configuration and seed policy;
4. fair baseline comparison;
5. retained raw or machine-readable output;
6. paired/statistical analysis when applicable;
7. provenance linking reported values to a run/artifact;
8. a documented limitation or counterexample.

If an experiment is exploratory, label it exploratory. If an outcome is commissioning evidence, call it commissioning evidence. If a claim is unsupported, keep it out of the abstract/README result summary.

## Pull requests

Keep PRs reviewable and evidence-scoped. Include motivation, changed scientific/engineering semantics, tests, artifact/provenance impact, and known limitations. Changes to a frozen experiment protocol should explain whether they invalidate or version existing retained evidence.

See [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) for the canonical repository map and [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) for claim boundaries.
