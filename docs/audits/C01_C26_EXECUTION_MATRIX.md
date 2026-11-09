# C01–C26 Execution Matrix

**Run source:** `b626d6e9b5bf8b8cf1ec87906597d767224f5f37` (main base); audit code commit: `dd80146672d7330a57bfabbf51ea8e25caff12b1` · **Environment:** Python 3.12.14, Linux-6.18.57-x86_64-with-glibc2.39.

The canonical suite wrote one manifest and individual CSVs only for commands that actually produced them. A skip is not a pass. All registered smoke experiments use controlled/synthetic evidence per the registry.

| ID | Experiment | Registry maturity | Execution | CSV rows | Artifact | SHA-256 |
|---|---|---|---|---:|---|---|
| C01 | `c01_learned_astar_comparison` | Research Prototype | **skipped_optional_dependency** | — | `artifacts/c01_learned_astar.csv` | `—` |
| C02 | `c02_uncertainty_calibration` | Research Prototype | **passed** | 3 | `artifacts/c02_uncertainty_calibration.csv` | `85d6b8aa5cc9d5aa…` |
| C03 | `c03_belief_risk_tradeoff` | Research Prototype | **passed** | 9 | `artifacts/c03_belief_risk_tradeoff.csv` | `843ee75749115e2c…` |
| C04 | `c04_recoverability_profile` | Research Prototype | **passed** | 4 | `artifacts/c04_recoverability_profile.csv` | `ff1256bfb9b60314…` |
| C05 | `c05_safe_mode_thresholds` | Research Prototype | **passed** | 12 | `artifacts/c05_safe_mode_thresholds.csv` | `e29c85fbcaf14ae5…` |
| C06 | `c06_resource_feasibility` | Research Prototype | **passed** | 5 | `artifacts/c06_resource_feasibility.csv` | `216d60c249f0e2f3…` |
| C07 | `c07_returnability_aware_nbv` | Research Prototype | **passed** | 5 | `artifacts/c07_returnability_aware_nbv.csv` | `7e990eb19474848b…` |
| C08 | `c08_ids_response_policy` | Experimental | **passed** | 5 | `artifacts/c08_ids_response_policy.csv` | `e51e633ae85c75a0…` |
| C09 | `c09_team_coordination` | Experimental | **passed** | 4 | `artifacts/c09_team_coordination.csv` | `9817e914df3c492e…` |
| C10 | `c10_human_ethics_policy` | Experimental | **passed** | 9 | `artifacts/c10_human_ethics_policy.csv` | `a84e790b8621f8bf…` |
| C11 | `c11_vlm_goal_validation` | Experimental | **passed** | 6 | `artifacts/c11_vlm_goal_validation.csv` | `4cf9891c5b56fa2b…` |
| C12 | `c12_risk_map_quality` | Experimental | **passed** | 8 | `artifacts/c12_risk_map_quality.csv` | `a2201d8d1b7ca28a…` |
| C13 | `c13_rollout_audit` | Experimental | **passed** | 5 | `artifacts/c13_rollout_audit.csv` | `e44e3053b2c39dc9…` |
| C14 | `c14_root_cause_attribution` | Experimental | **passed** | 5 | `artifacts/c14_root_cause_attribution.csv` | `6d112b3b7e0ffab3…` |
| C15 | `c15_neuromorphic_latency` | Experimental | **passed** | 6 | `artifacts/c15_neuromorphic_latency.csv` | `18e6fa2345249196…` |
| C16 | `c16_federated_tradeoffs` | Experimental | **passed** | 4 | `artifacts/c16_federated_tradeoffs.csv` | `4822917c0cdb4f69…` |
| C17 | `c17_topological_semantic_navigation` | Experimental | **passed** | 8 | `artifacts/c17_topological_semantic_navigation.csv` | `bf5ad86d36bfca56…` |
| C18 | `c18_shield_stress_test` | Experimental | **passed** | 6 | `artifacts/c18_shield_stress_test.csv` | `975671f22da14e8d…` |
| C19 | `c19_mission_plan_quality` | Documentation Concept | **passed** | 5 | `artifacts/c19_mission_plan_quality.csv` | `7af6893c4e3c9cba…` |
| C20 | `c20_failure_report_quality` | Experimental | **passed** | 3 | `artifacts/c20_failure_report_quality.csv` | `c501e295ed4a7f15…` |
| C21 | `c21_policy_safety` | Experimental | **passed** | 3 | `artifacts/c21_policy_safety.csv` | `b45f98ed9b851828…` |
| C22 | `c22_curriculum_strategies` | Experimental | **passed** | 3 | `artifacts/c22_curriculum_strategies.csv` | `4bdf516f914e7642…` |
| C23 | `c23_gaussian_mapping_quality` | Documentation Concept | **passed** | 2 | `artifacts/c23_gaussian_mapping_quality.csv` | `7825c316070e9821…` |
| C24 | `c24_nerf_uncertainty` | Documentation Concept | **passed** | 2 | `artifacts/c24_nerf_uncertainty.csv` | `214eacb9d6df6fb1…` |
| C25 | `c25_attack_impact` | Experimental | **passed** | 6 | `artifacts/c25_attack_impact.csv` | `98dce1b27c75ecfb…` |
| C26 | `c26_swarm_consensus` | Experimental | **passed** | 12 | `artifacts/c26_swarm_consensus.csv` | `c843d949c5b47267…` |

## Commands executed

```bash
python scripts/validate_contribution_registry.py
python scripts/run_contribution_suite.py --output-dir results/contribution_suite/full
python scripts/run_contribution_suite.py --only C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11 --output-dir results/contribution_suite/first_eleven
python scripts/run_contribution_suite.py --only C26 --output-dir results/contribution_suite/c26
```

## Outcome

- Full suite: 25 passed; 1 skipped; 0 failed after the C11 path fix.
- First-eleven batch: C02–C11 passed; C01 skipped because `torch` is unavailable.
- Independent C26 batch: passed.
- C11 had originally failed with `ModuleNotFoundError: dynnav` when invoked as a standalone runner. Its import path was repaired and rerun successfully.
- C01 has checkpoint files in the repository, but PyTorch is absent in this execution environment, so the checkpoint was not loaded and no learned-vs-classical measurement was made.

The manifest preserves stdout/stderr, status, duration, exact command, artifact row count and SHA-256 for each experiment.
