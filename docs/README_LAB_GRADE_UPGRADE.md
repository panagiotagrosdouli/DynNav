# Lab-Grade Upgrade Overview

This document summarizes the first DynNav v2 GitHub upgrade.

## Why this upgrade matters

The repository already contains many research-oriented modules. The next step is to make the project easier to evaluate by external robotics researchers.

A strong robotics repository should make three things obvious:

1. **What is implemented.**
2. **What evidence supports each claim.**
3. **How another researcher can reproduce or challenge the result.**

This upgrade adds repository-level documents and issue templates that push DynNav toward that standard.

## Added documents

| File | Purpose |
|---|---|
| `docs/DYNNAV_V2_RESEARCH_ROADMAP.md` | Defines the scientific direction, core research thesis, benchmark categories, and publication-readiness criteria. |
| `docs/BENCHMARK_PROTOCOL.md` | Defines common benchmark metadata, metrics, baselines, ablations, reporting rules, and failure-case logging. |
| `docs/CONTRIBUTION_READINESS_CHECKLIST.md` | Gives each module a repeatable checklist for scientific framing, reproducibility, metrics, baselines, ablations, and documentation. |
| `.github/ISSUE_TEMPLATE/research_module_upgrade.md` | Adds a structured GitHub issue template for upgrading a module. |
| `.github/ISSUE_TEMPLATE/benchmark_result.md` | Adds a structured GitHub issue template for reporting benchmark results. |

## Intended effect

This does not claim that DynNav is already state of the art. Instead, it gives the repository a clearer path toward being evaluated like a serious robotics research platform.

The main standard is:

```text
Every important claim should map to an experiment, every experiment should map to a metric, and every metric should be reproducible.
```

## Recommended next pull requests

1. Add a machine-readable benchmark manifest, for example `benchmarks/dynnav_benchmark_manifest.yaml`.
2. Add a result-table generator that reads module CSV outputs and produces a single Markdown summary.
3. Add a `run_smoke_benchmarks.py` script that checks lightweight experiments across the main modules.
4. Add a technical-report skeleton in `paper/` or `docs/technical_report.md`.
5. Add module readiness badges using the checklist levels.

## Suggested repository labels

Consider adding these GitHub labels:

- `research`
- `benchmark`
- `paper-readiness`
- `reproducibility`
- `safety`
- `uncertainty`
- `risk-aware-planning`
- `ros2`

## Review checklist for this PR

- [ ] Roadmap is accurate and does not overclaim.
- [ ] Benchmark protocol matches the repository's actual module structure.
- [ ] Issue templates are useful for future work.
- [ ] Future work is clearly separated from implemented results.
