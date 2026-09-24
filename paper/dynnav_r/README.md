# DynNav-R manuscript and evidence

`main.tex` is the current IEEE-style manuscript for the narrow DynNav study. The evidence boundary and current numerical claims are defined by [`evidence_manifest.json`](evidence_manifest.json) and cross-referenced in the repository's [`CLAIM_EVIDENCE_MATRIX.md`](../../CLAIM_EVIDENCE_MATRIX.md).

## Build

From this directory, use `latexmk -pdf main.tex` when available. Otherwise run:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The build requires IEEEtran, AMS math, booktabs, graphicx, hyperref, microtype, and TikZ packages.

## Reproduce the core evidence

From the repository root:

```bash
python scripts/run_history_information_gap_benchmark.py --out-dir results/history_information_gap
python scripts/run_heldout_history_generalization.py --seeds 500 --out-dir results/heldout_history_generalization
python scripts/run_geometric_heldout_benchmark.py --seeds 500 --output-dir results/geometric_heldout
python scripts/run_geometric_pareto_benchmark.py --seeds 500 --output-dir results/geometric_pareto
```

The exact CLI options for each runner are available with `--help`. Use the frozen experiment protocol and retained outputs when making manuscript-facing changes. Do not copy numbers into the paper unless they are regenerated or verified against the evidence manifest.

## Scope

The augmented state `(position, activated hazards)` is a standard Markovization of the declared finite model, not a novel general planning principle. The state-only marginal method is a restricted ablation that omits activated-hazard history. Evidence is synthetic and does not establish calibrated real-world probabilities, Gazebo efficacy, physical-robot efficacy, or a formal safety guarantee.
