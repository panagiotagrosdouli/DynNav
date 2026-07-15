# DynNav Repository Audit

This checkpoint tracks the repository-wide README and documentation hardening pass. A status is **verified** only when the referenced file or command has been inspected or executed.

| Finding | Severity | Evidence | Action | Status |
|---|---|---|---|---|
| `docs/README.md` contained unsupported claims of formal verification, 26 completed modules, ROS2/TurtleBot3/Gazebo/hardware validation, and numerical results | Critical | Previous `docs/README.md` content | Replaced with a conservative technical documentation index | Repaired |
| Root README needed one evidence-based research landing page | High | `README.md`, CI run #268, package metadata | Rebuilt status, architecture, formulation, install, quick-start, evaluation, limitations, responsible-use, citation and licence sections | Repaired |
| Top-level subsystem directories lacked navigation and maturity guidance | High | Missing README responses through GitHub Contents API | Added subsystem-specific READMEs for configs, source, package, scripts, tests, assets, results, paper and website | Repaired for verified paths |
| Generated GIF requested for the root landing page does not exist | Medium | `assets/demo.gif` returns 404 | Retained the existing conceptual SVG and stated that GIF generation is pending | Open artifact gap |
| Recursive README inventory could not be executed | High | Execution container cannot resolve `github.com`; connector exposes files but not a complete recursive tree | Record blocker and require clean-checkout inventory before completion | Open — required |
| Recursive Markdown-link, asset, and anchor validation has not run | High | No executable checkout available | Run automated validators in a network-enabled environment or CI | Open — required |
| Docker commands remain unverified | Medium | No Docker execution in current session | Build and run the root Dockerfile before claiming reproducibility | Open — required |
| ROS2/Nav2, Gazebo, and hardware claims require independent evidence | Critical | Current audit and root README | Preserve prototype/planned labels and prohibit deployment or safety claims | Open research milestones |

## README files changed in this branch

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

## Claims and evidence policy

- **Implemented** requires source plus executable test or CI evidence.
- **Research Prototype** means code or scaffolding exists but deployment validation is incomplete.
- **Experimental** means evidence is limited, commonly synthetic or grid-world based.
- **Planned** means no complete implementation is claimed.
- **Pending Validation** means an implementation or command exists without all required evidence.
- **Simulation Only** must never be described as hardware evidence.
- **Hardware Validation Required** means no physical-robot conclusion is supported.

## Commands already evidenced by GitHub Actions

PR #64, run #268 successfully exercised:

```bash
pytest
python scripts/run_all.py --config configs/default.yaml --smoke --out-dir results/ci_smoke
python scripts/run_benchmarks.py --config configs/default.yaml --smoke --out-dir results/ci_benchmarks
cd website && npm install --no-audit --no-fund
cd website && npm run typecheck
cd website && npm run build
```

## Remaining acceptance checks

```bash
find . -type f -iname 'README*' | sort
# Run a recursive Markdown link and local asset checker.
# Run a Markdown anchor checker.
# Validate each command extracted from every README.
docker build -t dynnav .
docker run --rm dynnav
```

ROS2/Nav2, Gazebo, and hardware checks require the corresponding environments and are not replaced by Python CI.

Completion of the user's recursive README request is **not claimed** until the clean-checkout inventory and automated link/anchor/command audits pass.
