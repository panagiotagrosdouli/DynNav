# DynNav — Start Here

> **Navigation guide, not a new scientific claim.** DynNav is a research repository with one canonical publication track, a robotics implementation, interactive labs and a collection of exploratory research modules. Different directories have different validation levels.

## Choose your path

| I want to… | Start here | What to expect |
|---|---|---|
| Understand the central idea in two minutes | [Main README](../README.md) | Executive explanation and limitations |
| Read the current research paper | [Canonical IEEE manuscript](../paper/dynnav_r/main.tex) | History-conditioned safe-return under action-triggered hazards |
| Verify paper results | [Evidence manifest](../paper/dynnav_r/evidence_manifest.json) · [Claim–evidence matrix](../CLAIM_EVIDENCE_MATRIX.md) | Artifact provenance and supported vs unsupported claims |
| Read core Python algorithms | [dynnav/planners](../dynnav/planners/) · [hazard model](../dynnav/commitment_hazard.py) | Planner and stochastic-closure implementation |
| Explore research experiments | [dynnav/experiments](../dynnav/experiments/) · [protocol](BENCHMARK_PROTOCOL.md) | Mechanism, held-out, execution and adversarial tests |
| Build the robotics integration | [ROS 2 Nav2 C++](../ros2_ws/src/dynnav_nav2_cpp/) · [benchmark](../ros2_ws/src/dynnav_nav2_benchmark/) | Plugin and integration evidence, not a hardware-safety claim |
| Explore the interactive lab | [Streamlit app](../app/README.md) | Synthetic planning and controlled demos |
| Find web application code | [Next.js workspace](../apps/web/) · [FastAPI](../apps/api/) | Application layer |
| Browse the 26 research modules | [Contributions](../contributions/README.md) · [maturity matrix](CONTRIBUTION_MATURITY_MATRIX.md) | Mixed-maturity experimental programme |
| Continue C01-ERGO | [C01 module](../contributions/01_learned_astar/) · [ERGO boundaries](../contributions/01_learned_astar/ERGO_NOVELTY_BOUNDARIES.md) | Exploratory prototype, not a published result |
| Understand the full tree | [Repository guide](REPOSITORY_GUIDE.md) | Canonical, exploratory, retained, and legacy distinctions |
| Reproduce/test | [Tests](../tests/) · [CI workflows](../.github/workflows/) · [reproducibility guide](REPRODUCIBILITY.md) | Automated checks and research contracts |

## Evidence levels matter

**Core publication track:** `dynnav/`, `paper/dynnav_r/`, `ros2_ws/src/dynnav_nav2_cpp/`, `ros2_ws/src/dynnav_nav2_benchmark/` and the retained evidence referenced in the paper manifest.

**Supporting applications:** `app/`, `apps/` and related website components are interfaces and demonstrations, not additional proof of robotics efficacy.

**Exploratory and historical code:** `contributions/`, `nav_research/`, `neural_uncertainty/`, `cybersecurity_ros2/`, `photogrammetry_module/`, `ig_explorer/`, other earlier modules and historical logs remain available for research continuity. Their presence does not mean they all support the current paper.

**C01–C26:** 7 research prototypes, 16 experimental, 3 documentation concepts in the programme registry. C27 is a separate theory proposal, not an independently validated experimental contribution.

## Minimal research workflow

1. Read the [central question](../README.md) and [manuscript](../paper/dynnav_r/main.tex).
2. Check the [evidence manifest](../paper/dynnav_r/evidence_manifest.json) before repeating any paper numbers.
3. Follow reproducible experiment scripts and existing frozen protocols rather than silently editing old CSVs.
4. For new work, use a feature branch and PR; attach test commands, seed/config, evidence boundaries and negative results.
5. Promote claims to the publication track only after the [claim–evidence matrix](../CLAIM_EVIDENCE_MATRIX.md) and bibliography are updated.

## Organization policy

This document adds navigation **without moving/deleting files**, breaking imports, rewriting retained results or reclassifying experimental maturity. Structural refactoring should be performed later, one independently tested subsystem at a time.

**Current research status:** active research prototype. No certification, universal superiority or physical-robot efficacy is claimed.
