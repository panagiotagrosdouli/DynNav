# C07 — historical Next-Best-View exploration code evidence

This directory is the historical NBV/active-exploration branch of **C07**, alongside the canonical registered `contributions/07_next_best_view/` folder.

The controlled registered C07 experiment `c07_returnability_aware_nbv` was executed successfully in [GitHub Actions #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587); its runner is `contributions/07_next_best_view/experiments/eval_returnability_aware_nbv.py`. That smoke verifies only the canonical returnability-aware scoring fixture. It **does not** execute each additional historical frontier/exploration script here.

All files in this historical directory are nonetheless included in `scripts/audit_contributions_c02_c26.py` file-by-file inspection (source compilation, output parsing, plots, SHA-256). The full workflow artifact is `c02-c26-per-file-and-per-contribution-execution`.

See [canonical C07 execution evidence](../07_next_best_view/EXECUTION_EVIDENCE.md). Real sensor-derived frontier evidence, ROS2 closed-loop exploration, real robot perception and physical exploration safety remain unverified by these synthetic tests. **Verified physical C07 trials: 0.**
