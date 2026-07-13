# DynNav Reproducibility Report

**Status:** In progress — completion is not claimed.

## Verification environment

| Item | Value |
|---|---|
| Date | 2026-07-13 |
| Repository | `panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments` |
| Branch | `feature/dynnav-complete-redesign-repair` |
| Base branch | `main` |
| Base head inspected | `f8741220129493ba674131787b3df989f785076d` |
| Operating system | Linux command sandbox; exact distribution not recorded because checkout did not begin |
| Python | Not yet verified against a clean checkout |
| Node | Not yet verified against a clean checkout |
| npm | Not yet verified against a clean checkout |
| Docker | Not yet verified against a clean checkout |

## Clean-clone attempt

Command:

```bash
git clone https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git dynnav_repo
```

Result: **Blocked before checkout**.

```text
fatal: unable to access 'https://github.com/panagiotagrosdouli/DynNav-Dynamic-Navigation-Rerouting-in-Unknown-Environments.git/':
Could not resolve host: github.com
```

The failure is an environmental DNS/network limitation, not evidence that the repository itself passes or fails installation.

## Required clean-checkout protocol

The following commands remain mandatory and must be recorded with exact exit codes and generated artifact paths:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m compileall src scripts tests
ruff check .
black --check .
pytest -q
python scripts/run_all.py --mode smoke
python scripts/run_all.py --mode validate

docker build -t dynnav .
docker run --rm dynnav
docker run --rm -v "$(pwd)/results:/app/results" dynnav

cd website
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
```

## Current verified interface gaps

The complete protocol cannot pass in the repository state inspected at the start of this branch because:

- `scripts/run_all.py` does not support `--mode smoke` or `--mode validate`.
- `website/package.json` has no `lint` script.
- `website/package.json` has no `test` script.
- the current CI workflow does not run `ruff check .`.
- the current CI workflow does not run `black --check .`.
- the current website workflow uses `npm install` rather than `npm ci`.

These are tracked as required failures in `AUDIT.md` and `STATUS.yaml`.

## Generated outputs

No output is listed as regenerated or validated in this report yet. Existing tracked media and results must be treated as unverified until their generation commands, decoding, deterministic inputs, and repository references have been audited from a complete checkout.

## Optional integrations

ROS 2, Nav2, Gazebo, physical hardware, and optional MP4 encoders have not been validated. They must be reported as optional environmental stages, not as core software failures and not as completed integrations.

## Clean-clone status

**NOT PASSED.**
