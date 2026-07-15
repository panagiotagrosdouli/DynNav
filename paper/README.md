# Paper-facing material

This directory contains manuscript-oriented notes and artifacts for a possible DynNav research paper.

**Status:** **Planned / Pending Validation.** A manuscript structure or conceptual contribution list is not evidence of a completed publication, accepted paper, statistically supported claim, or validated robotics system.

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
