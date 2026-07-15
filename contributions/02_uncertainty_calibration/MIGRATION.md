# Contribution 02 migration note

`02_uncertainty_calibration` is the canonical Contribution 02 module.

It subsumes the former `02_uncertainty_estimation` placeholder by covering uncertainty estimation, informativeness auditing, calibration, and downstream planner integration. The obsolete placeholder contained no implementation and referenced a non-existent `eval_uncertainty.py` entry point.

Use:

```bash
python contributions/02_uncertainty_calibration/experiments/eval_uncertainty_calibration.py
```

Do not recreate a second `02_*` contribution directory. Estimation methods such as EKF/UKF should be documented or implemented inside this canonical module when they are backed by repository code and tests.
