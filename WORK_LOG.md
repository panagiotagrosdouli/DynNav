# DynNav Work Log

## 2026-07-15 — all-Markdown evidence pass

### Scope

The requested scope is every Markdown file in the repository, not only README files. The pass includes technical documentation, contribution READMEs, benchmark notes, reports, blockers, reproducibility records, generated Markdown summaries and paper-facing material.

### Completed in this branch

- created `docs/MARKDOWN_AUDIT.md`;
- created `docs/MARKDOWN_STYLE_GUIDE.md`;
- linked Markdown governance from `docs/README.md`;
- added `scripts/audit_markdown.py` to recursively inventory every `*.md` file;
- added local path, asset and Markdown-anchor validation;
- added warnings for high-risk unsupported claim phrases;
- added a required GitHub Actions Markdown job;
- configured the job to upload a machine-readable `markdown_audit.json` artifact even when validation fails.

### Why this is required

The command execution container cannot resolve `github.com`, while GitHub Actions receives a complete checkout. Running the recursive validator in CI provides the authoritative inventory and broken-reference list without guessing repository paths.

### Evidence inherited from merged PRs

- PR #64 CI run #268 passed the Python 3.10, 3.11 and 3.12 suites, smoke commands, website dependency installation, website type checking and website build.
- PR #66 repaired the root and top-level README evidence boundary.

### Remaining work

The first Markdown CI run must complete. Every reported broken link, missing asset and invalid anchor must be repaired. Each remaining Markdown file must then be inspected for implementation accuracy and unsupported scientific, ROS2, Gazebo, hardware, benchmark or safety claims.

Completion is not claimed until the CI inventory reports every Markdown path and all required checks pass.

## 2026-07-15 — README and documentation hardening

### Baseline

- PR #64 completed GitHub Actions run #268 successfully.
- PR #64 was merged into `main` as commit `28717f0dc2f04ae0f35b2b8b29fad3f168ced2cc`.
- PR #66 repaired the root and top-level README evidence boundary.

### README work completed

Updated or added:

- `README.md`
- `configs/README.md`
- `src/README.md`
- `src/dynnav/README.md`
- `scripts/README.md`
- `tests/README.md`
- `docs/README.md`
- `assets/README.md`
- `results/README.md`
- `paper/README.md`
- `website/README.md`

### Critical documentation repair

The previous `docs/README.md` claimed formal verification, 26 completed research modules, ROS2 Humble integration, TurtleBot3, Gazebo, real-robot validation and numerical performance results. Those statements contradicted the root README, CI evidence and repository audit. The file was replaced with an evidence-based documentation index.

### Completion state

The README pass is merged, but the repository-wide all-Markdown audit remains active in the branch recorded above.
