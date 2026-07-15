# Scripts

This directory contains repository-level experiment, benchmark, media, and smoke-test entry points.

**Maturity:** Scripted Python workflows are **Implemented** where exercised by CI. Full clean-clone, Docker, link, media, ROS2, and Gazebo validation remains **Pending Validation**.

## Verified CI entry points

```bash
python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/ci_smoke
python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/ci_benchmarks
```

Other documented entry points include:

```bash
python scripts/run_research_suite.py --out-dir results/research_suite
python scripts/generate_research_assets.py
python scripts/make_demo_gif.py
```

Before relying on an optional script, inspect its `--help` output and source. Do not treat generated synthetic artifacts as hardware or Gazebo evidence.

## Inputs and outputs

- Inputs: YAML files under [`../configs/`](../configs/README.md).
- Outputs: generated files under [`../results/`](../results/README.md) and media under [`../assets/`](../assets/README.md).
- Tests: relevant behavior is covered under [`../tests/`](../tests/README.md).

## Troubleshooting

- Run from the repository root so relative paths resolve consistently.
- Install with `python -m pip install -e ".[dev]"` before invoking scripts.
- MP4 generation may require an optional codec; a GIF or explicit fallback is not proof that MP4 generation succeeded.
- Preserve non-zero exits for required failures.

See the [root README](../README.md) and [`../docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md).
