# DynNav — Five-minute research tour

A guided entry point for visitors, students, reviewers and potential collaborators.

## 1. Understand the problem
An autonomous robot may travel to a goal through a passage that triggers a future closure. A shortest-path planner can reach the goal yet lose a safe route home. Different executed paths reaching the same cell can activate different closure hazards. [Main explanation](../README.md).

## 2. Read the method
The paper-focused planner represents its state as `(position, activated hazards)`, where hazards are activated by **executed transitions**, not merely planned ones. Follow the [hazard semantics](../dynnav/commitment_hazard.py), [history-aware A*](../dynnav/planners/commitment_aware_astar.py) and [exact return-connectivity oracle](../dynnav/recoverability_belief.py).

## 3. Inspect evidence critically
Start from the [IEEE manuscript](../paper/dynnav_r/main.tex), then verify claimed results against the [evidence manifest](../paper/dynnav_r/evidence_manifest.json) and [claim-evidence matrix](../CLAIM_EVIDENCE_MATRIX.md). Controlled experiments do not establish real-world safe operation. Negative results are part of the scientific evidence.

## 4. Examine the robot integration
See the [C++ Nav2 plugin](../ros2_ws/src/dynnav_nav2_cpp/) and [Gazebo benchmark infrastructure](../ros2_ws/src/dynnav_nav2_benchmark/). Distinguish interface/build validation from demonstrated comparative execution efficacy, and from real robot deployment.

## 5. Explore the broader research programme
The [contributions index](../contributions/README.md) describes C01–C27, which span learned heuristics, uncertainty, robotics safety, exploration, multimodal AI and multi-robot systems. These are **not** 27 independently validated research discoveries. Refer to the [maturity matrix](CONTRIBUTION_MATURITY_MATRIX.md).

## 6. Try or contribute
- Python setup and quality checks: [CONTRIBUTING](../CONTRIBUTING.md).
- Interactive controlled demonstrations: [Streamlit lab](../app/README.md).
- Full repository map and paths: [START_HERE](START_HERE.md).
- Research results: always report configuration, seeds, baseline, confidence intervals where applicable, and failure cases.

**Status:** Academic research prototype, not certified autonomous navigation or a claim of physical-robot efficacy.
