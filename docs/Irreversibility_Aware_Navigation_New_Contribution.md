## Irreversibility-Aware Navigation

This repository includes experiments studying irreversibility constraints in navigation under uncertainty and their relationship to risk-weighted planning.

### Key components

- irreversibility-map construction from uncertainty and local geometry;
- hard irreversibility-constrained planning with feasibility thresholds;
- safe-mode planning with controlled threshold relaxation;
- adaptive threshold selection through global feasibility-aware estimation;
- failure analysis distinguishing local and global infeasibility modes.

### Core experiments

| Experiment | Historical entry-point name |
|---|---|
| Bottleneck feasibility sweep | `run_irreversibility_bottleneck_sweep.py` |
| Hard-versus-soft comparison | `plot_hard_vs_soft_comparison.py` |
| Safe-mode activation analysis | `run_irreversibility_safe_mode_sweep.py` |
| Adaptive multi-start threshold analysis | `run_minimax_tau_multistart.py` |
| Failure taxonomy analysis | `plot_failure_taxonomy.py` |

The names above are retained for traceability. They are not repository links unless matching files are committed at documented paths.

### Theoretical statement

The current theory document discussing why hard irreversibility constraints are not generally reducible to scalar risk weighting is:

- [Proposition: Irreversibility versus Risk Weighting](Proposition_Irreversibility_vs_Risk_Weighting.md)

This material should be treated as a research proposition and counterexample analysis, not as a formal safety certificate or a universal guarantee. Experimental claims require traceable scripts, configurations, raw results, and regenerated figures.
