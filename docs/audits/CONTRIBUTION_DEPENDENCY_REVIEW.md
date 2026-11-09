# Contribution Dependency Review

The registry graph describes intended relationships, not verified dependencies. The C01-C26 suite invokes separate runners and does not prove end-to-end integration.

## Coherent integration candidates

- **Core planning:** C03 risk input + C04 structural returnability + C06 resource feasibility + C18 runtime shield can feed C00 only through explicit typed semantics and one frozen objective/constraint contract. Exact history-conditioned return probability remains distinct from structural C04 metrics.
- **Perception to planning:** C02 calibration and C12 occupancy forecast may feed C03 after a common occupancy target, time horizon, and calibration dataset are defined. C11 only checks structured semantic outputs; it does not invoke a VLM.
- **Supervision/security:** C08 anomaly signal and C25 injected faults could feed C05, but response latency and detector error rates require ROS 2 closed-loop validation. C18 numerical tests are not a proof.
- **Multi-robot:** C09 conflict accounting and C26 in-process consensus can share map/task contracts; C16 federation is not communication validation. No distributed ROS 2 network experiment was run.
- **Learning:** C13, C21 and C22 are fixture-level in the canonical suite. Connecting them before trained-model and evaluation contracts exist would couple unvalidated assumptions.

## Integration evidence found

The repository has separate modules, dashboards, registries and ROS 2 packages. This audit ran the registered contribution suite, not composed runtime pipelines. Website cards now link each source and experiment runner; this is discovery integration only. C00 and C04 have related but distinct recoverability semantics and require a common experimental interface before composing.

## Recommended order

1. Freeze C00's returnability definition and data contracts.
2. Validate C03/C04/C06 inputs against reference cases.
3. Add one composed planning study with matched routes, fixed seeds, and ablations.
4. Add C05/C18 supervision only after command-level closed-loop tests exist.
5. Extend to perception/multi-robot where the same outcomes and provenance can be measured.
