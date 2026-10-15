# C01-ERGO baseline audit (initial, non-execution review)

Status: **partial source audit**. No baseline rerun or claims of new speedup.

## Canonical sources examined
- `experiments/astar_learned_heuristic.py`: generic four-neighbour A*, Manhattan baseline, raw learned heuristic and Manhattan clipping; default `allow_missing_model=True`.
- `experiments/statistical_validation.py`: four obstacle-density regimes (0.1–0.4), 100 tasks each, checks only path cost and outcomes.
- `experiments/admissibility_audit.py`: reverse BFS cost-to-go and sampled admissibility/consistency tests.
- `code/learned_heuristic.py`: 11-input, two-hidden-layer (64 units each by default) ReLU MLP.
- `models/`: multiple retained .pt checkpoints; training provenance and hashes not yet independently verified.

## Key findings
1. A raw network estimate is neither proven admissible nor consistent. The generic A* implementation closes nodes without reopening, so optimality is not assured for raw predictions. Equality of sampled path costs is not a proof.
2. Manhattan clipping is admissible in the declared four-connected unit-cost grid, but not necessarily consistent; clipping does not dominate Manhattan.
3. Silent fallback risk: `allow_missing_model=True` can replace learned inference with Manhattan. Confirm checkpoint load and report model hashes before interpreting comparisons.
4. A separate fixed-grid evaluation in `eval_astar_learned.py` includes checkpoint construction inside each trial's learned timing window; distinguish initialization cost from per-query and warm-model timings.
5. Different C01 files use different model defaults/paths. Unify model selection in future confirmation runs, but do not modify historical data.
6. Current benchmark samples reachable tasks from synthetic grid distributions. Report transfer claims only after held-out topologies and preprocessing/training leakage audit.
7. Existing runtime figures from README: 1.17 ms classic vs 18.31 ms raw learned on an independent 100-task example (historical report, not reproduced here).

## Proposed prototype and proof boundary
`code/ergo_optimal.py` retains classical `f=g+h_Manhattan` as the PRIMARY priority and uses neural predictions ONLY as a SECONDARY tie-breaker for nodes with equal primary f. Thus arbitrary neural values cannot cause an f-higher node to be expanded before an f-lower one. Since Manhattan is consistent on the declared graph, the first popped goal has shortest-path cost. This is not a proof for weighted edges, arbitrary motion models or dynamic maps changing *during* one search. Replanning on a changed map is a new independent search.

The cache key hashes the complete current grid plus node and goal. Safe reuse is restricted to an identical map/goal. It is intentionally **not** localized invalidation, classical search-state reuse, LPA*, or any novel learning method.

## Mandatory next validation
- Execute the 400-task and 100-task baselines with explicitly resolved checkpoint path, `allow_missing_model=False`, model SHA256, packages and hardware metadata.
- Compare against original raw learned A*, clipped learned A*, weighted A*, rational lazy heuristic search and LPA*/D* Lite where relevant.
- Record cold/warm model load times, neural calls, latency distributions, memory, expansions, exact BFS optimality, and confidence intervals.
- Test a nontrivial dynamic sequence and held-out topology families.
- Establish literature novelty separately; selective heuristic evaluation and incremental search are established prior art.
