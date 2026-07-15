# Repository-wide Markdown audit

This document tracks the audit of every Markdown file in DynNav.

## Scope

The pass includes root documentation, technical documentation, subsystem READMEs, benchmark notes, contribution READMEs, reports, blockers, reproducibility records, work logs, and paper-facing Markdown.

## Evidence rule

Every document must distinguish:

- **Implemented** — source exists and executable test or CI evidence exists.
- **Research Prototype** — code or scaffold exists, but deployment evidence is incomplete.
- **Experimental** — evaluated only in limited or synthetic settings.
- **Planned** — no complete implementation is claimed.
- **Pending Validation** — implementation exists but required validation has not completed.
- **Simulation Only** — evidence is simulation evidence, not hardware evidence.
- **Hardware Validation Required** — no physical-robot result is available.

## Current critical findings

1. Historical Markdown contained claims of formal verification, ROS2/Nav2 integration, Gazebo/TurtleBot3 and hardware validation, trained learning systems, and numerical improvements that were not supported by the current green CI baseline.
2. The root and top-level navigation READMEs were repaired in PR #66.
3. Contribution and benchmark Markdown still requires file-by-file verification against the implementation.
4. A recursive Markdown link, local asset and anchor checker is still required before completion.

## Required completion checks

```bash
find . -type f -iname '*.md' -print | sort
# Run recursive local-link and asset-reference validation.
# Run Markdown anchor validation.
# Extract and execute documented commands in their declared environments.
```

Docker, ROS2/Nav2, Gazebo, browser and hardware commands must be validated separately. Python CI does not substitute for those environments.

## Completion state

Completion is not claimed until the inventory and validators cover every Markdown file in a clean checkout.
