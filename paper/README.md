# Paper-facing material

> **Current canonical manuscript:** [`dynnav_r/main.tex`](dynnav_r/main.tex). The remaining root-level DynNav-R draft and its original gap analysis are historical exploratory material; they are not current claims or publication evidence. Read [`dynnav_r/README.md`](dynnav_r/README.md), [`dynnav_r/NOVELTY_BOUNDARIES.md`](dynnav_r/NOVELTY_BOUNDARIES.md), and the repository [`CLAIM_EVIDENCE_MATRIX.md`](../CLAIM_EVIDENCE_MATRIX.md) for the active scope.

This directory contains manuscript-oriented notes and artifacts for a possible DynNav research paper.

**Status:** **Planned / Pending Validation.** A manuscript structure or conceptual contribution list is not evidence of a completed publication, accepted paper, statistically supported claim, or validated robotics system.

## Additional provisional study

[`../RESEARCH_DISCOVERY.md`](../RESEARCH_DISCOVERY.md) records a separate exploratory robustness study of uncertain action-trigger execution and noisy crossing observations. It includes a selective literature map, rejected candidate questions, the exact belief update, synthetic results, and explicit limits. The study is **not** part of the current canonical manuscript and does not support a novelty claim yet; it needs systematic literature screening and broader experiments before manuscript integration.

## Evidence requirements

Paper figures and tables should be generated from raw files under [`../results/`](../results/README.md). Reported values must retain their configuration, seed, command, and commit provenance.

Before a contribution is stated as a final research result, the repository needs:

- fair baseline and ablation definitions;
- multi-seed experiments;
- confidence intervals and effect sizes;
- failure-case reporting;
- clear synthetic, simulation, and hardware labels;
- reproducible figure and table scripts.

## Proposed framing

The current central question concerns dynamic replanning under occupancy risk, uncertainty, recoverability, and mission-level supervision. ROS2/Nav2, Gazebo, and physical-robot integration remain separate validation milestones.

See [`../docs/REPOSITORY_AUDIT.md`](../docs/REPOSITORY_AUDIT.md), [`../docs/EVALUATION_PROTOCOL.md`](../docs/EVALUATION_PROTOCOL.md), and the [root README](../README.md).
