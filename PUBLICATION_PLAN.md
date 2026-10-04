# Publication Plan

## Current paper

**When the Same Place Is Not the Same State: History-Conditioned Safe-Return Planning under Action-Triggered Topology Hazards**

The manuscript, code, retained synthetic/geometric evidence, ROS 2/Nav2 integration and strict action-triggered Gazebo mechanism probes are integrated into the current repository. The project is past the earlier J0–J3 workshop-planning stage.

## Current scientific story

The paper tests whether **executed path history contains recoverability-relevant information that a state-only future-risk model discards when robot actions activate future topology hazards**.

Current retained evidence covers:

- same-state/different-history information separation;
- exact augmented-state planning;
- a critical-cut approximation and adversarial failure boundary;
- analytic mechanism checks;
- paired stochastic execution in controlled families;
- held-out probability/horizon generalization;
- three frozen hand-authored geometric topologies;
- soft-history vs hard-safe-return Pareto behavior;
- ROS 2 Jazzy / Nav2 integration;
- protocol-valid action-triggered Gazebo execution and measurement evidence.

The strict Gazebo reruns do **not** support a stable comparative DynNavHistory-vs-DynNavShortest efficacy effect, so no such claim is made.

## Completed publication hardening

- The frozen action-triggered Gazebo scenario has been executed with paired planner conditions and deterministic shared event realizations.
- Retained strict probes enforce adjacent executed-transition observation, blocker injection/observation checks, explicit trial validity and recovery assessment.
- Invalid-trial semantics are separated from mission and irreversibility outcomes.
- The C++ Nav2 planner, persistent executed-history state and benchmark contracts are covered by ROS CI.

## Remaining publication-hardening milestones

1. **Probability miscalibration stress:** freeze nominal-vs-true trigger-probability offsets and test decision sensitivity without retuning after outcomes.
2. **Partial-observability stress:** evaluate delayed or noisy hazard revelation while preserving the distinction between latent hazard activation and robot-observed information.
3. **Correlated closure stress:** add a model/baseline that does not assume independent future closures when the scenario deliberately violates independence.
4. **Broader Gazebo efficacy study, if claimed:** predeclare a larger execution study and analysis plan before inspecting outcomes; the current mechanism probes are integration evidence only.
5. **Submission audit:** run the full-main validation set on the release commit, compile the manuscript, regenerate/verify publication-facing tables and numbers from retained artifacts, audit bibliography/provenance and inspect the final PDF.

## Optional stronger validation

A physical TurtleBot3 study would materially strengthen the robotics story but is not required to describe the current simulation evidence accurately. If performed, use a static known map and AMCL first; verify TF/odometry/scan/costmaps, cap speed and acceleration, establish a physical perimeter and human e-stop, record exact robot/sensor/configuration metadata, and separate commissioning trials from the frozen evaluation set.

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
