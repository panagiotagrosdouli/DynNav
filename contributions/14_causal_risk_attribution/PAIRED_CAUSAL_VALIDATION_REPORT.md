# C14 — Actually executed paired structural counterfactual attribution

**Date:** 2026-11-10. [Successful actual C14 workflow #42792663356](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42792663356).

## Experimental design and evidence hierarchy

C14 uses a **hand-coded Structural Causal Model**, not causal structure learned from actual Dingo failures. The new `experiments/eval_paired_counterfactuals.py` performed 250 reproducible *synthetic fault-injection episodes* (seed 2026), with 50 injected episodes per candidate causal variable and **same exogenous noise** for factual and do-intervention outcomes. Each intervention uses an explicitly declared neutral value: zero for error/risk variables, one for map accuracy and obstacle detection. Interventions are model operations, **not interventions carried out on physical hardware**. The file retains all rankings and injected episode provenance.

The pre-existing 5-case root cause script was also executed and reported top-1 **40%** on its five legacy cases, which are not paired or identically distributed to the new evaluation.

## Observed real CI results

| Injected failure cause | N | Top-1 injected-cause identification | Mean true-cause rank |
|---|---:|---:|---:|
| Sensor noise | 50 | 100% | 1.00 |
| Localization error | 50 | 2% | 2.00 |
| Map accuracy | 50 | 12% | 1.94 |
| Obstacle detection | 50 | 100% | 1.00 |
| Path risk | 50 | 100% | 1.00 |
| **All cases** | **250** | **62.8%** | — |

**Negative scientific result:** Localization and map-accuracy injections are often attributed to another upstream node, under the deliberately simple hand-coded graph and current intervention scoring. The method does not reliably recover all injected causes and should NOT be described as accurate physical root-cause identification.

The **250-case and 5-case** top-1 rates are not directly comparable generalization estimates due to different case generation and evaluation designs. More episodes drawn from one hand-crafted SCM do not prove that this causal graph represents real robot failure dynamics.

## Implementation and verification

- `experiments/eval_paired_counterfactuals.py`: paired factual/counterfactual evaluations, finite checks, explicit neutral reference values, per-cause and overall scores, SHA-256 of source SCM.
- `tests/test_paired_counterfactuals.py`: numerical pair matching, neutral reference values, fail-closed invalid inputs and reproducible 50-episode fixtures.
- `.github/workflows/c14-paired-causal.yml`: actual Python 3.12 execution of legacy benchmark plus 250 new cases; independent validation of 250 rows, root attribution ranks and physical evidence fields.
- CI artifact `c14-paired-injected-causal-attribution-evidence` contains `counterfactual_trials.csv`, `summary.json`, and `legacy_root_cause.csv`.

The experiment is useful for **internal SCM consistency and diagnostic algorithm evaluation**. It is not an identifiable causal effect estimated from real robot observations. The impact score is `factual_outcome - counterfactual_outcome` with a fixed noise realization, not a Shapley contribution. The rankings and intervention neutral values are domain/model assumptions.

## Missing research evidence

There is no independent physical experiment proving the SCM arrows, no logged actual C14-selected corrective robot action, no randomized controlled physical intervention, and no real failure ground truth. Source Dingo recorded motion from LILocBench cannot retrospectively prove C14 was installed. **Verified physical C14 autonomous robot trials: 0.**

To test causal validity, first acquire safe, independently annotated failure logs with confirmed interventions and independent sensors/ground-truth outcome, fit/test the SCM on disjoint sessions, compare against noncausal anomaly and graph-ablated baselines, report uncertainty, and only perform physical interventions under onsite operator authorization with emergency stop.
