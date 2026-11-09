# C07 — executable evidence and honest validation boundary

**Status:** One actual registered **synthetic** experiment executed and passed in [GitHub Actions run #42702357587](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42702357587). This does not mean the scientific hypothesis, all historical scripts or a physical robot have been fully validated.

## Registered hypothesis

Returnability-aware next-best-view scoring preserves safer retreat options than information-gain-only selection.

## Exact executable experiment

Experiment ID: `c07_returnability_aware_nbv`. Source: `contributions/07_next_best_view/experiments/eval_returnability_aware_nbv.py`.

```bash
python scripts/run_contribution_suite.py --only C07 --fail-on-skip --output-dir results/contribution_audit/C07
```

The runner produces `manifest.json`, `summary.md` and a non-empty experimental CSV with content SHA-256. The joint [C02–C26 workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c02-c26-exhaustive.yml) runs the 25 modules **one by one** and retains independent artifacts for each.

## Baselines, primary metrics and boundaries

- **Baselines:** [Information-gain-only NBV].
- **Registered metrics:** [information_gain, path_risk, returnability, connectivity, classic_score, safe_score].
- **Evidence level:** `synthetic`.
- **Specific limitation:** Candidate views are hand-authored fixtures rather than sensor-derived frontiers.

Full C02–C26 file-level integrity (SHA-256, AST compile, archived CSV/NPZ/PyTorch/PNG/SVG checks) is tracked in `scripts/audit_contributions_c02_c26.py` and reported in the CI artifact `c02-c26-per-file-and-per-contribution-execution`. Structural file checks do **not** mean all historic experiments, saved weights, training or physical-world claims have been reproduced.

## Two historical locations
The canonical registered runner lives in `contributions/07_next_best_view/`. The historical `contributions/07_nbv_exploration/` code and outputs are included in the same C07 file inventory. They are **not two independent contributions**, and the canonical smoke does not execute every historical NBV script.

## What is still required for stronger scientific or hardware claims

Independently validate the data source and separation of training/calibration and held-out maps or sites; run appropriate real sensor/robot recordings where the algorithm actually consumes those observations; preserve failures and independently checked baseline measurements; and attach provenance (code commit, dataset hashes, fixed seeds, time, hardware and software). For claims about actual **onboard physical-robot execution**, obtain a new supervised ROS 2/Nav2 integration run on a named robot with an emergency stop, true synchronized motion/planner logs and explicit proof that this contribution was active.

**Physical robot C07 execution verified by this CI: 0 trials.** A synthetic fixture, historical bag playback, neural checkpoint file or ROS service success must never be relabelled as a physical-robot result.
