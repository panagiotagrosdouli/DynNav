# Engineering and Scientific Audit

Date: 2026-07-08

## Audit method

The repository was inspected through the available GitHub connector, including repository metadata, recent commits, `README.md`, `READMEbig.md`, package metadata, core navigation modules, planning modules, tests, demo generation, documentation, and website scaffold. Direct full-tree cloning was not available in the execution environment, so the audit is limited to accessible files and code-search results.

## High-priority findings

| Rank | Finding | Motivation | Action taken |
|---:|---|---|---|
| 1 | Research concepts existed but were distributed across modules without a single integrated API. | Reviewers need traceable interfaces for uncertainty, risk, recoverability, monitoring, and safety modes. | Added `dynnav.research_modules` with typed reports, supervisor, monitor, and research-stack facade. |
| 2 | Website contained placeholder cards rather than paper-companion content. | Portfolio presentation should communicate methods, outputs, and limitations without exaggeration. | Expanded `website/app/page.tsx` with motivation, architecture, pipeline, benchmark status, downloads, and roadmap. |
| 3 | Demo generation produced media but did not expose risk-mode annotations. | A robotics demo should show the decision state, not only a moving path. | Enhanced `scripts/make_demo_gif.py` with mission-risk evaluation and annotated animation text. |
| 4 | Documentation needed stronger claim discipline. | Scientific quality depends on separating implemented, prototype, and planned components. | Expanded `docs/RESEARCH_OVERVIEW.md` and `docs/SYSTEM_ARCHITECTURE.md`. |
| 5 | New research-layer behavior needed regression tests. | Safety and monitoring logic should not be untested documentation. | Added `tests/test_research_modules.py`. |

## Scientific audit

Strengths:

- The repository already frames navigation as risk-aware and uncertainty-aware rather than shortest-path only.
- Existing primitives are typed and suitable for deterministic experiments.
- The README explicitly distinguishes implemented, prototype, and planned components.
- The package has modern Python metadata, lint/test tooling, and CI-oriented dependencies.

Weaknesses:

- Some advanced claims, such as formal guarantees, ROS2 deployment, and learning-augmented navigation, require additional evidence before publication-level claims.
- Synthetic benchmarks are useful for reproducibility but cannot replace robot logs or ablation studies.
- Risk thresholds are interpretable engineering parameters, not calibrated safety certificates.
- The website and figures must be regenerated from scripts after benchmarks run.

## Engineering audit

Strengths:

- `src/dynnav/` provides a reusable Python package with typed dataclasses.
- `pyproject.toml` defines packaging, development tools, and test configuration.
- Test files already cover smoke-level planning and scenario generation.
- Demo generation and website scaffolds exist.

Weaknesses:

- Some concepts were still spread across separate modules without a single high-level stack API.
- Placeholder website text reduced perceived research maturity.
- Runtime monitoring decisions required clearer event records and cooldown behavior.
- Generated artifacts are not committed by this change; they must be produced in an environment with plotting/video dependencies.

## Remaining limitations

This transformation improves structure, documentation, tests, website content, and research APIs. It does not prove formal safety, validate on hardware, tune thresholds on real logs, or guarantee ROS2 plugin compilation. Those require future experiments and should remain explicitly labeled as future work.
