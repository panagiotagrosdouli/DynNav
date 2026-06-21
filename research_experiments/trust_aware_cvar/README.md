# Calibration-Aware and Trust-Aware Risk Navigation — DynNav Research Extension

This is a complete, **executed** research artifact (not a proposal) implementing and
evaluating a Trust-Aware CVaR Planner on top of the DynNav project's existing modules.

## Quick facts
- 32,400 simulated episodes actually executed (not fabricated) across 50 maps × 6 environment
  families × 7 planners × 5 experimental sweeps.
- Full statistical battery: Welch t-tests, Mann–Whitney U, one-way ANOVA, Cohen's d, bootstrap 95% CIs.
- All numbers in `paper/paper.md` are read directly from `results/*.csv`.

## Structure
```
core/
  grid_env.py        # 6 environment families (static/dynamic/dense/adversarial/sensor_corruption/low_visibility)
  planners.py         # A*, D*, D* Lite (full incremental), CVaR-A*, RiskAware-A*, DynNavCurrent, TrustAwareCVaR
  calibration.py       # ECE measurement + controllable miscalibration injection
  trust.py             # 4-component trust estimator (calibration, consistency, perception, anomaly)
  safety_shield.py      # Discrete CBF-filter analogue of DynNav Contribution 18
  adversarial.py        # FGSM / PGD / sensor-spoofing attack injectors (DynNav Contribution 25 style)
benchmark/
  run_experiments.py    # Episode simulator + Phase 3-5 orchestration (CLI: --n_maps --size --episodes_per_map)
analysis/
  stats_analysis.py     # Phase 7 statistical analysis -> results/statistical_summary.csv
  plots.py              # Phase 8 publication figures -> figures/*.png
  latex_tables.py        # Phase 8 LaTeX tables -> results/tables/*.tex
results/                # All CSV outputs (raw + aggregated)
figures/                # All PNG plots (300dpi)
paper/paper.md          # Full IEEE-style paper (Phases 9-10)
```

## Reproducing / scaling up
```bash
# Pilot scale used for this paper (fast, ~6 minutes total):
python -m benchmark.run_experiments --n_maps 50 --size 26 --episodes_per_map 12

# Camera-ready / full original spec scale (50 maps x 100 episodes):
python -m benchmark.run_experiments --n_maps 50 --size 26 --episodes_per_map 100

python -m analysis.stats_analysis
python -m analysis.plots
python -m analysis.latex_tables
```

## Honesty note
This artifact intentionally reports null and mixed results (Sections 5.2, 5.3, 5.5 of the
paper) rather than only favorable ones. The reduced experimental scale (12 vs. the originally
requested 100 episodes/map) is documented, not hidden, and the code is parameterized to
re-run at full scale without modification.
