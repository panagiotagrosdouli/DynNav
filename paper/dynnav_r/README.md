# DynNav-R Manuscript

This directory contains the LaTeX manuscript scaffold for the recoverability-aware navigation paper track.

## Build

From `paper/dynnav_r/`:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

A `latexmk` installation can instead run:

```bash
latexmk -pdf main.tex
```

## Experimental artifact workflow

Generate randomized benchmark results:

```bash
python ../../benchmarks/fragile_commitment/random_benchmark.py \
  --seeds 100 \
  --output random_topology_results.csv
```

Run paired hypothesis tests:

```bash
python ../../benchmarks/fragile_commitment/paired_tests.py \
  random_topology_results.csv \
  --baseline risk_only \
  --candidate recoverability_aware \
  --output-csv paired_tests.csv \
  --markdown paired_tests.md
```

Generate figures:

```bash
python ../../benchmarks/fragile_commitment/paper_figures.py \
  random_topology_results.csv \
  --output-dir ../figures/fragile_commitment \
  --format pdf
```

Generate tables:

```bash
python ../../benchmarks/fragile_commitment/paper_tables.py \
  random_topology_results.csv \
  paired_tests.csv \
  --output-dir ../tables/fragile_commitment
```

## Evidence policy

The manuscript contains explicit TODO markers where quantitative findings, citations, environment details, or inferential decisions still require validation. Do not replace those markers with claims until the corresponding commands have been executed and their outputs have been inspected.

The benchmark is synthetic and does not establish formal safety, ROS 2 integration, or hardware validation.
