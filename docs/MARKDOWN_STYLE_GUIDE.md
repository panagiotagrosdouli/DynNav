# Markdown evidence and maintenance guide

Use this guide for every Markdown file in DynNav.

## Required structure

A technical document should state its purpose, maturity, verified implementation, inputs, outputs, commands, limitations and related files. Not every document needs every heading, but no document may imply evidence that does not exist.

## Maturity labels

| Label | Meaning |
|---|---|
| Implemented | Source exists and is exercised by tests or CI. |
| Research Prototype | Executable or scaffolded, but not deployment-ready. |
| Experimental | Evidence is limited or synthetic. |
| Planned | No complete implementation is claimed. |
| Pending Validation | Implementation exists but required checks are incomplete. |
| Simulation Only | Evidence comes from simulation. |
| Hardware Validation Required | No physical-robot evidence is available. |

## Claims

Do not claim formal verification, safety guarantees, real-time operation, state-of-the-art performance, statistical significance, ROS2/Nav2 loading, Gazebo execution or hardware validation without traceable evidence.

Quantitative statements must identify the result file, configuration, seed set, command and statistical method. Example or placeholder values must be labelled as examples.

## Links and commands

- Prefer relative links for repository files.
- Do not link missing images, GIFs, videos or reports.
- Commands must run from the directory stated in the document.
- Optional dependencies and environment requirements must be explicit.
- Generated files must identify their generating script.

## Duplication

The root README is the research landing page. Nested READMEs describe their directory. Technical details belong in `docs/`; generated evidence belongs in `results/`; manuscript-facing material belongs in `paper/`.

See [`MARKDOWN_AUDIT.md`](MARKDOWN_AUDIT.md) and the [root README](../README.md).
