# C04 Returnability and Irreversibility Summary

- Tau sweep success rate: 0.267
- Minimum feasible tau: 0.85
- Safe-mode success rate: 1.000
- Safe-mode relaxed cases: 15 / 26
- Mean tau relaxation gap: 0.0800
- Safe-mode path length: 45
- Mean irreversibility on safe-mode path: 0.4800
- Max irreversibility on safe-mode path: 0.8500
- Returnability sweep success rate: 1.000
- Returnability meanR at mu=0: 0.0416
- Returnability meanR at largest mu: 0.1507

## Interpretation

The hard irreversibility threshold admits paths only above the minimum feasible tau, while safe mode preserves feasibility by relaxing tau to the smallest viable threshold. This provides an explicit recoverability mechanism instead of silently failing when the nominal threshold is too strict.