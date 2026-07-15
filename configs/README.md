# DynNav configurations

This directory contains versioned YAML inputs for deterministic DynNav runs.

**Maturity:** Implemented configuration files; validation depth is currently a research-prototype concern.

## Primary entry points

- [`default.yaml`](default.yaml): default input used by the CI smoke and benchmark commands.
- [`benchmark.yaml`](benchmark.yaml): benchmark configuration used by the `dynnav-benchmark` command when present.
- [`research_suite.yaml`](research_suite.yaml): deterministic research-suite contract when present.

## Usage

From the repository root:

```bash
python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/smoke
python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/benchmarks
```

The installed benchmark entry point is:

```bash
dynnav-benchmark --config configs/benchmark.yaml --out-csv results/benchmarks/dynnav_benchmark.csv --summary results/benchmarks/summary.md
```

## Configuration policy

- Keep seeds, map dimensions, planner weights, starts, goals, and output paths explicit.
- Do not report a result without the exact configuration and seed.
- Invalid ranges or incompatible weights should fail with actionable errors; comprehensive typed validation is **Pending Validation**.
- ROS2, Nav2, Gazebo, and hardware parameters are not validated by the default Python CI.

See [`../docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md), [`../docs/EVALUATION_PROTOCOL.md`](../docs/EVALUATION_PROTOCOL.md), and the [root README](../README.md).
