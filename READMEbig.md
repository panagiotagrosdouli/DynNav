# DynNav — Legacy Extended README

> **Status:** archival documentation entry point.

This file previously contained a long-form project description with links to generated PDFs, Streamlit pages, scripts, result files, and experimental artifacts that are not present on the current `main` branch. To prevent broken documentation and unsupported research claims, the legacy content has been replaced by this validated index.

## Start here

- [Primary README](README.md) — verified project status, installation, quick start, architecture, limitations, and roadmap.
- [Documentation index](docs/README.md) — technical documentation grouped by responsibility.
- [Repository audit](docs/REPOSITORY_AUDIT.md) — authoritative implemented/prototype/planned capability boundaries.
- [Research overview](docs/RESEARCH_OVERVIEW.md) — research questions and current scope.
- [Mathematical formulation](docs/MATHEMATICAL_FORMULATION.md) — objective terms and notation.
- [Evaluation protocol](docs/EVALUATION_PROTOCOL.md) — comparison rules and metric requirements.
- [Reproducibility guide](docs/REPRODUCIBILITY.md) — configuration, seeds, commands, and provenance.
- [Contribution index](contributions/CONTRIBUTIONS_README.md) — research-module navigation.
- [Paper material](paper/README.md) — publication-facing documents and evidence requirements.

## Evidence policy

Only artifacts committed to the repository and linked through a valid repository path should be treated as available evidence. Planned deep-dive PDFs, dashboards, experiment outputs, ROS2 demonstrations, Gazebo runs, or hardware results must not be presented as existing until they are committed with traceable provenance.

Passing tests or deterministic grid-world experiments does not establish a formal safety guarantee, state-of-the-art performance, ROS2/Nav2 readiness, Gazebo validation, or real-robot validation.

## Historical material

The previous extended narrative can be recovered from Git history when needed for archival comparison. New project-facing documentation should be added to the appropriate file under [`docs/`](docs/) and linked from the primary [`README.md`](README.md).
