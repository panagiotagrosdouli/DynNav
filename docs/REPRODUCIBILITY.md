# Reproducibility

## Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Alternatively:

```bash
docker build -t dynnav .
docker run --rm dynnav
```

## Benchmarks

```bash
dynnav-benchmark \
  --config configs/benchmark.yaml \
  --out-csv results/benchmarks/dynnav_benchmark.csv \
  --summary results/benchmarks/summary.md
```

## Figures

```bash
python scripts/generate_research_assets.py
python scripts/make_demo_gif.py
```

## Determinism

Synthetic scenarios are generated from explicit seeds. Reported benchmark tables must include the configuration file and seed range used to generate the result.

## Known reproducibility gaps

ROS 2, Gazebo, and hardware experiments require platform-specific dependencies and are not part of the default CI job. Those experiments should include environment manifests and raw logs before being described as validated.
