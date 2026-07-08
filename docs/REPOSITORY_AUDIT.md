# DynNav Repository Audit

This audit records the scientific and engineering state of the repository after the autonomous transformation pass. It is intentionally conservative: it distinguishes working code from prototypes and planned research.

## Severity ranking

| Severity | Area | Finding | Action taken |
|---|---|---|---|
| Critical | Scientific honesty | Benchmark outputs must not be presented as evidence before deterministic runs are generated and reviewed. | Added explicit Implemented / Prototype / Planned status policy and research-suite configuration. |
| High | Architecture | Earlier code concentrated several research ideas in flat modules, which made it harder to expose planning, risk, uncertainty, recoverability, and supervision as separate concepts. | Added `src/dynnav/lab_grade.py` as a typed integration layer with registry, fields, rerouting, and safety primitives. |
| High | Reproducibility | Experiment expectations were not fully encoded as a single deterministic suite manifest. | Added `configs/research_suite.yaml` with seeds, statuses, metrics, and expected outputs. |
| High | ROS2/Nav2 | Integration should be presented as a prototype unless a compiled Nav2 plugin and launch-tested package exist. | Added ROS2/Nav2 documentation that labels package, plugin, BT, RViz, and bag playback items as Prototype. |
| Medium | Evaluation | Metrics existed conceptually, but ablation status needed clearer separation from reported results. | Added deterministic episode metric API and tests; marked ablations as Prototype until result files exist. |
| Medium | Safety | Runtime safety policy must be described as a supervisor prototype, not a certified safety controller. | Added threshold-based `SafetySupervisor` with explicit limitations. |
| Medium | Documentation | Mathematical notation and mission-level safety definitions needed one canonical reference. | Added formal mathematical formulation documentation. |
| Low | Presentation | The README was already research-oriented but did not yet emphasize the new lab-grade audit output. | Added a branch-ready change set and can update README after CI validation. |

## Scientific audit

DynNav now states the central research question directly: how can a robot reroute online in unknown dynamic environments while reasoning about uncertainty, risk, recoverability, and mission safety? The current code supports deterministic grid-world experiments and interpretable planning costs. It does not yet support hardware-validated safety claims, formal completeness under dynamic obstacles, or state-of-the-art comparisons.

## Engineering audit

The added primitives are dependency-light, typed, deterministic, and covered by pytest. They avoid ROS2 dependencies so the default Python CI remains fast. ROS2/Nav2 work remains a documented prototype scaffold until plugin code is compiled and exercised in a ROS workspace.

## Documentation audit

The repository has research overview, architecture, reproducibility, and roadmap material. This pass adds a formal formulation and ROS2/Nav2 maturity statement so readers can distinguish current implementation from planned lab integration.

## Reproducibility audit

The new `configs/research_suite.yaml` enumerates seeds, metrics, and expected outputs. The suite is a configuration contract; it is not a substitute for measured results. Any generated CSV, JSON, figure, or GIF should be committed only when produced by scripts and traceable to a seed.

## Visual presentation audit

Publication-quality figures and demo assets should be generated only from scripts. Existing and future images must avoid fabricated benchmark numbers. Placeholder logos and diagrams are acceptable when labeled as placeholders or schematics.

## Current status summary

| Component | Status | Evidence | Limitation |
|---|---|---|---|
| A* / Dijkstra baselines | Implemented | `src/dynnav/lab_grade.py`, `tests/test_lab_grade.py` | Grid-world validation only |
| Risk-aware A* | Implemented | existing planner + tests | No hardware validation |
| Risk / uncertainty fields | Implemented | deterministic NumPy fields + tests | Simplified belief model |
| Recoverability field | Prototype | reachability-based field | Expensive for large grids |
| Dynamic rerouting | Prototype | threshold + cooldown supervisor | No continuous-time robot dynamics |
| Safety supervisor | Prototype | threshold policy + tests | Not certified safety control |
| ROS2/Nav2 integration | Prototype | docs/scaffold | No compiled plugin claim |
| Formal guarantees | Planned | roadmap | Requires future proof and experiments |
