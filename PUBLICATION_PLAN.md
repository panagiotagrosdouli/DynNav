# Publication Plan

## Current paper

**When the Same Place Is Not the Same State: History-Conditioned Safe-Return Planning under Action-Triggered Topology Hazards**

The manuscript, code, retained synthetic/geometric evidence and ROS 2/Nav2 integration are already in `main`. The project is therefore past the earlier J0–J3 workshop-planning stage.

## Current scientific story

The paper tests whether **path history contains recoverability-relevant information that state-only future-risk models discard when robot actions activate future topology hazards**.

Current evidence covers:

- same-state/different-history information separation;
- exact augmented-state planning;
- a critical-cut approximation and adversarial failure boundary;
- analytic mechanism checks;
- paired stochastic execution in controlled families;
- held-out probability/horizon generalization;
- three frozen hand-authored geometric topologies;
- soft-history vs hard-safe-return Pareto behavior;
- ROS 2 Jazzy / Nav2 integration.

## Remaining publication-hardening milestones

1. **Action-triggered Gazebo execution:** run the frozen `(174,189) -> (175,189)` trigger scenario with paired planner conditions and common event realizations. Retain raw trial data and validity diagnostics.
2. **Execution integrity:** require observed adjacent executed transitions, valid blocker injection, global-costmap observation and explicit recovery assessment. Invalid trials are reported separately, not converted into failures.
3. **Probability miscalibration stress:** freeze nominal-vs-true trigger-probability offsets and test decision sensitivity without retuning after outcomes.
4. **Partial-observability stress:** evaluate delayed or noisy hazard revelation while preserving the distinction between latent hazard activation and robot-observed information.
5. **Correlated closure stress:** add a model/baseline that does not assume independent future closures when the scenario deliberately violates independence.
6. **Submission audit:** regenerate all manuscript tables/claims from retained artifacts, verify bibliography/provenance and inspect the compiled PDF.

## Optional stronger validation

A physical TurtleBot3 study would materially strengthen the robotics story but is not required to describe the current simulation paper accurately. If performed, use a static known map and AMCL first; verify TF/odometry/scan/costmaps, cap speed and acceleration, establish a physical perimeter and human e-stop, record exact robot/sensor/configuration metadata, and separate commissioning trials from the frozen evaluation set.

## Release artifacts

A submission snapshot should archive:

- source commit SHA;
- paper PDF and source;
- `paper/dynnav_r/evidence_manifest.json`;
- frozen protocols/configurations/seeds;
- raw CSV/JSON artifacts and summary files;
- ROS/Gazebo logs or bags for execution-level claims;
- analysis scripts and figure/table generators;
- exclusion/invalid-trial log;
- known negative cases and approximation failures.

## Submission gate

Do not add or strengthen an efficacy claim if its underlying run is missing retained provenance, if trial validity is ambiguous, or if the wording exceeds the evaluated domain. Negative or null results remain scientifically useful when the protocol, baseline and measurement contracts are strong.

The central novelty claim must remain narrow: **action-triggered degradation of safe-return connectivity with history-conditioned state aliasing**, not generic recoverability, generic safe-return planning, generic history dependence or generic endogenous uncertainty.
