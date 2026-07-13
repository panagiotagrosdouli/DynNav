# DynNav Repository Audit

This audit tracks the repository-wide redesign, repair, and release-quality pass. A status is **verified** only when the listed command has actually completed successfully in a clean environment.

| Issue | Severity | Affected file or area | Root cause | Proposed fix | Verification command | Final status |
|---|---|---|---|---|---|---|
| Clean-clone validation has not run | Critical | Repository-wide | The current maintenance environment can access repository files through the GitHub integration but cannot resolve `github.com` from the command runner | Run the complete clean-clone protocol in GitHub Actions and a network-enabled local environment | See `REPRODUCIBILITY_REPORT.md` | Open — required |
| CI does not execute repository-wide Ruff | High | `.github/workflows/ci.yml` | Ruff is limited to the mapping package and one test file | Add `ruff check .` as a required job step and repair every reported issue | `ruff check .` | Open — required |
| CI does not execute Black validation | High | `.github/workflows/ci.yml` | No Black step is defined | Add `black --check .` and format root causes rather than excluding files | `black --check .` | Open — required |
| CI uses a split and ad-hoc pytest strategy | High | `.github/workflows/ci.yml`, `pyproject.toml`, `tests/` | Tests are divided between an embedded Python launcher and per-file timeout shell loop; marker categories are not registered | Classify tests with registered markers and make the default suite meaningful and deterministic | `pytest -q`; marker-specific commands | Open — required |
| Website scripts are incomplete | High | `website/package.json` | Only `dev`, `build`, `start`, and `typecheck` scripts exist | Add real lint and test scripts with supporting configuration/tests | `npm run lint`; `npm run test` | Open — required |
| Website CI is not a clean install | Medium | `.github/workflows/ci.yml` | CI uses `npm install` instead of `npm ci` | Commit a valid lockfile and use `npm ci` | `cd website && npm ci` | Open — required |
| Website lint and tests are absent from CI | High | `.github/workflows/ci.yml` | Website job only type-checks and builds | Add required lint and test steps after implementing them | `npm run lint`; `npm run test` | Open — required |
| Unified runner does not support required modes | High | `scripts/run_all.py`, `src/dynnav/research_pipeline.py` | `run_all.py` only forwards to a pipeline CLI supporting `--smoke`; no `--mode smoke|demo|research|validate` exists | Separate orchestration from experiment execution and implement stage summaries/exit codes | `python scripts/run_all.py --mode smoke`; `python scripts/run_all.py --mode validate` | Open — required |
| Configuration loading lacks typed validation | High | `src/dynnav/research_pipeline.py`, `configs/` | Defaults are inserted into an untyped dictionary; ranges, coordinates, planner names, and path constraints are not validated before execution | Add explicit validation with actionable user-facing errors | Run invalid/valid configuration regression tests | Open — required |
| Generated path manifest contains empty paths | High | `src/dynnav/research_pipeline.py` | `planned_paths.json` is generated from trajectory rows with `"path": []`, not from actual planner outputs | Record each actual planned/rerouted path and test the manifest | Generate smoke output and inspect `planned_paths.json` | Open — required |
| Multiple distinct figures are generated from the same generic risk/uncertainty plot | High | `src/dynnav/research_pipeline.py`, `assets/figures/`, `results/figures/` | Placeholder loop writes differently named files from an identical plotting routine | Implement figure-specific deterministic generation and label all synthetic outputs | Regenerate artifacts and compare deterministic hashes | Open — required |
| MP4 availability is printed as a normal output even after fallback | Medium | `src/dynnav/research_pipeline.py` | MP4 export exceptions create a fallback note, but the CLI still prints the missing MP4 path as part of a generic completion list | Report generated, skipped optional, and failed required artifacts separately | Run with and without an MP4 codec | Open — required |
| Docker default command only runs tests | Medium | `Dockerfile` | Container behavior does not demonstrate a useful DynNav run or mounted-results workflow | Define a useful deterministic default and retain a documented test target | `docker build -t dynnav .`; both required `docker run` commands | Open — required |
| Docker build installs development dependencies in the runtime image | Medium | `Dockerfile` | Single-stage image installs `.[dev]` and copies tests | Use an intentional validation image or multi-stage/runtime split; document image purpose | Inspect image and run container validation | Open — required |
| README CI badge is not enough to establish reproducibility | Medium | `README.md`, `.github/workflows/ci.yml` | Existing workflow does not cover all commands claimed by the release criteria | Keep only accurate badges and add reproducibility status only after full pipeline passes | Inspect badge target and successful workflow run | Open — required |
| Repository-wide README/link/media inventory is incomplete | High | All documentation and assets | GitHub file integration does not provide a recursive executable checkout in the current environment | Run recursive inventory/link/media validators from a clean checkout and record every item | `python scripts/run_all.py --mode validate` plus link/media checks | Open — required |

## Evidence inspected

- `README.md`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `Dockerfile`
- `website/package.json`
- `scripts/run_all.py`
- `src/dynnav/research_pipeline.py`

This file intentionally does not mark inferred or unexecuted work as passed.
