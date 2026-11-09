# Contribution Follow-up Repairs

**Scope:** Targeted source review and engineering corrections for C07, C13, C14, C16, and C26 after the canonical C01–C26 suite. This follow-up does not claim that all modules have equivalent evidence.

## Changes and evidence

| ID | Repair | Tests / experiment | Result and evidence level |
|---|---|---|---|
| C07 | Validate candidate values and weights for finiteness, domain, and nonnegative scoring parameters. | `python -m unittest discover -s contributions/07_next_best_view/tests -v` | 2 tests pass; unit-level synthetic scoring only. |
| C13 | Add seeded reproducible action-sequence generation, config validation, and strict observation/action/candidate shape checks. Mark RSSM as an untrained prototype. | `python -m unittest discover -s contributions/13_latent_world_model/tests -v`; canonical rollout audit passed. | 2 tests pass; model remains random-weight and untrained. No predictive accuracy claim. |
| C14 | Use dynamic topological ordering, reject invalid SCM graphs/interventions, pair factual and counterfactual noise, and intervene at node reference values. Limit ranking to outcome ancestors. | `python -m unittest discover -s contributions/14_causal_risk_attribution/tests -v`; `python contributions/14_causal_risk_attribution/experiments/eval_root_cause_attribution.py --n-samples 200 --out /tmp/c14.csv` | 4 tests pass. Synthetic SCM: top-1 0.60, mean true-cause rank 2.20, mean counterfactual reduction 0.338. Map accuracy and obstacle detection ranked fourth. Evidence is conditional on the hand-specified graph. |
| C16 | Replace parameter clipping/local noise with server-side clipping of client deltas and Gaussian noise on their uniform mean. Enforce fixed cohort, uniform weights, positive clip bound, and basic per-round composition constraints. Clarify that the server sees raw client updates and training data are synthetic. | `python -m unittest discover -s contributions/16_federated_nav_learning/tests -v`; `python contributions/16_federated_nav_learning/experiments/eval_federated_tradeoffs.py --rounds 8 --n-clients 6 --out /tmp/c16.csv` | 4 tests pass. Synthetic MSE: no-noise weighted/uniform 0.3220; central-DP uniform ε=2: 1.2690; ε=1: 1.3029. Six clients, eight rounds. This shows utility loss in this fixture, not a navigation result or deployed privacy guarantee. |
| C26 | Correct scope to centralized median/MAD proposal selection; remove self-reported confidence weighting; validate proposals; abstain below quorum; return path-cost pair from one proposal; validate returned paths; define one selection pass and approximate upload/broadcast counts. | `python -m unittest discover -s contributions/26_swarm_consensus/tests -v`; `python contributions/26_swarm_consensus/experiments/eval_swarm_consensus.py --out /tmp/c26_followup.csv` | 4 tests pass. One-map synthetic batch: success 1.00, cost accuracy 1.00, cost-outlier recall proxy 0.465, estimated messages mean 35.2. Perfect scores apply only to the fixed scenarios; no distributed agreement or BFT property is established. |

## Canonical suite

`python scripts/validate_contribution_registry.py` reports exactly 26 registered contributions and 26 experiment records with no errors or warnings. The final full suite completed with C02–C26 passing and C01 skipped because PyTorch is unavailable. The suite ran to `/tmp/dynnav_followup_full_final`; C14/C16/C26 were also rerun individually after correction. No real dataset, ROS 2/Gazebo, or physical robot evidence was added by this follow-up.

## Remaining scientific limits

- C07's checks validate score inputs, not sensor-derived frontier quality.
- C13 has no training loop/checkpoint; it remains a random-weight model prototype.
- C14 evaluates attribution only against its own assumed synthetic structural causal model.
- C16's central client-level mechanism depends on fixed full-cohort participation, replace-one adjacency, uniform aggregation, and basic composition. It is not local DP, secure aggregation, or a production accountant.
- C26 is centralized and synthetic. The name `BFTConsensus` is retained for compatibility, with explicit scope correction in code and docs.

**Source revision:** published follow-up commit SHA to be added after push.
