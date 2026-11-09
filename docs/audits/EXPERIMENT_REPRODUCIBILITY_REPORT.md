# Experiment Reproducibility Report

## Commands and results

The registry validator reported 26 contributions, 26 experiments, no errors or warnings. After fixing the C11 import path, the full suite completed with 25 passed and C01 skipped because `torch` is unavailable. The first-eleven batch had C02-C11 pass and C01 skip; separate C26 passed. Full manifests preserve exact commands, stdout/stderr, status, duration, artifact row count and SHA-256. Outputs are under `results/contribution_suite/{full,first_eleven,c26}`.

## Reproducibility limitations

- This environment had no `pytest`; `pytest -q` and `python -m pytest -q` both could not start.
- It had no `torch`, so C01 `.pt` files were not evaluated.
- Runs are one configured smoke execution, not repeated multi-seed replications. Several use fixtures, not datasets.
- C01-C27 audit implementation and evidence records identify code commit `753a5f8251994b18bf4979005073257af337c038`; unchanged C00 source is based on main commit `b626d6e9b5bf8b8cf1ec87906597d767224f5f37`.

## Reproduction

```bash
python scripts/validate_contribution_registry.py
python scripts/run_contribution_suite.py --output-dir results/contribution_suite/full
python scripts/run_contribution_suite.py --only C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11 --output-dir results/contribution_suite/first_eleven
python scripts/run_contribution_suite.py --only C26 --output-dir results/contribution_suite/c26
```
