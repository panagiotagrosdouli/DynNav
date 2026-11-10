# C14 — Paired SCM counterfactuals and actual Dingo odometry, without false causal claims

**Date:** 2026-11-10. **Verified experiment:** [GitHub Actions run #42792457762](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42792457762) passed, including **5 new targeted tests**, genuine original Dingo bag SHA-256 confirmation, the synthetic known-root fixture, and offline analysis of 24 source-recorded speed-change events.

## Mathematical defect fixed and independently tested

The earlier SCM root-cause routine computed one observational baseline under a fixed observed-noise vector but compared it against counterfactuals with new independent random draws for unspecified exogenous variables. Thus even an unrelated variable could receive spurious nonzero causal attribution. The revised implementation uses **matched exogenous noise** for each observed/counterfactual pair and uses the same realization bank for all candidate causes. The query evaluator also topologically sorts declared DAGs and rejects unknown variables, directed cycles, nonfinite interventions and invalid Monte Carlo counts.

The test suite verifies an unrelated exogenous variable gets exactly zero paired counterfactual effect, fixed-noise ranking is independent of Monte Carlo count, custom DAG order works and malformed queries fail closed.

## Explicit negative result on synthetic known-root benchmark

The same [run #42792457762](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42792457762) independently re-executed the five known injected-cause benchmark fixtures, using 80 noise draws per attribution. With the corrected paired-noise SCM, **top-1 attribution accuracy was 0.400**, average true-cause rank **2.80** and mean hypothetical counterfactual reduction **0.338** in internal model units.

**This is not high causal root-cause accuracy**. It is a negative/inconclusive outcome on a tiny source-defined, handcrafted synthetic benchmark; the absolute reduction is a model-specific index, not collision probability.

## Actually physically recorded source diagnostic

Source original LILocBench Clearpath Dingo `dynamics_0.bag`, original SHA-256 `df4abb923df1bb1ff46326abab8667188f4bc17e7ae12ea16905e9d632470c58`. The code actually decoded **2,328** physical odometry messages, formed **2,327** finite-speed steps, used the first **1,163** step-changes to define a robust descriptive normalization of speed-change magnitude, and inspected the remaining **1,163** steps. The 24 largest speed changes were selected for explicit model-based, hypothetical `do(sensor_noise=0)` queries.

**Critical claim separation:** The physically recorded value is the *change in odometry-derived speed*, not a known sensor-noise variable. Acceleration, steering, slip and genuine dynamics can cause that change; the normalization is an assumed proxy. The SCM graph and causal equations were **not learned from the Dingo recording**. No physically administered intervention occurred and no actual collision outcome or accident probability was observed. The output `collision` is only a scalar value internal to the hand-defined SCM. The real recording was not obtained while C14 controlled the Dingo.

## Exact reproduction

```bash
python -m pytest -q contributions/14_causal_risk_attribution/tests

python contributions/14_causal_risk_attribution/experiments/eval_root_cause_attribution.py \
  --n-samples 80 --out results/c14_real_dingo/original_synthetic_scm_fixture.csv

python contributions/14_causal_risk_attribution/experiments/eval_real_dingo_hypothetical_scm.py \
  /path/to/original/dynamics_0.bag \
  --examples 24 --out results/c14_real_dingo/assumed_scm_odometry_events.json
```

Dedicated CI workflow: [`.github/workflows/c14-real-dingo-hypothetical-scm.yml`](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c14-real-dingo-hypothetical-scm.yml). CI uploads the exact source-hash-bound diagnostic JSON and benchmark CSV, **not the original ROS bag**.

## What is NOT proven

Real causal structure identification, causal effect of deliberate robot actions on hazards, matched real intervention/control outcomes, measured physical collision probabilities, robust domain generalization, full ROS 2/Nav2 risk planning integration and physical C14 navigation are all unverified. **Physical C14-controlled robot trials: zero.**

Stronger causal hypotheses require measured confounders, identifiable interventions in a safe experimental protocol, independent held-out physical episodes, propensity/selection-bias analysis, reproducible baseline claims and explicit physical robot safety commissioning.
