# Generated results

This directory is the destination for benchmark metrics, summaries, figures, manifests, and optional videos.

**Status:** Deterministic synthetic result generation is **Experimental**. No file in this directory should be interpreted as Gazebo, hardware, field, or certified-safety evidence unless its manifest explicitly establishes that provenance.

## CI smoke outputs

The required smoke commands are:

```bash
python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/ci_smoke
python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/ci_benchmarks
```

The installed benchmark command can write CSV and Markdown summaries:

```bash
dynnav-benchmark --config configs/benchmark.yaml --out-csv results/benchmarks/dynnav_benchmark.csv --summary results/benchmarks/summary.md
```

## Required provenance

Every reportable experiment should record:

- commit SHA and command;
- configuration path and seed;
- software and operating-system versions;
- scenario and planner identifier;
- generated files;
- success or explicit failure reason.

Do not delete failed episodes or manually type paper values when they can be generated from raw results.

See [`../docs/EVALUATION_PROTOCOL.md`](../docs/EVALUATION_PROTOCOL.md), [`../docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md), [`../assets/README.md`](../assets/README.md), and the [root README](../README.md).
