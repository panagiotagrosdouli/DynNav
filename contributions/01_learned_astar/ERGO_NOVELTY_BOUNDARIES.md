# C01-ERGO: novelty and validation boundaries

**Stage:** exploratory engineering prototype; *not* a publishable novel result yet.

## Verified neighboring literature
- Karpas et al. (2018), *Rational deployment of multiple heuristics in optimal state-space search*, Artificial Intelligence 256, 181–210. DOI: 10.1016/j.artint.2017.11.001. Expensive-heuristic scheduling and rational lazy evaluation are prior art.
- Koenig, Likhachev and Furcy (2004), *Lifelong Planning A*.*, Artificial Intelligence 155, 93–146. DOI: 10.1016/j.artint.2003.12.001. Incremental reuse after map changes is prior art.
- Yonetani et al. (2021), *Path Planning using Neural A* Search*, ICML (PMLR 139). Neural A* search guidance is prior art.

## Claim matrix
| Claim | Evidence | Status |
|---|---|---|
| Neural tie-break preserves optimality with primary consistent Manhattan f | Graph-search argument + pending regression execution | Proposed proof + tests |
| Exact-map cache never reuses across different grid contents | SHA256 whole-grid key with goal/node | Implemented |
| Faster end-to-end planning | No new measured neural experiment | Unsupported |
| Local cache invalidation / dynamic incremental search | Not implemented | Unsupported |
| Distribution-shift gating | API hook only; no calibrated gate | Unsupported |
| Uniquely novel compared with rational lazy or incremental search | Incomplete literature audit | Unsupported |

## Planned falsification
Run historical baselines unchanged, then 400 paired benchmarks, cold/warm model measurements, tests on map edits and goal changes, domain shift, competent incremental baselines, and 95% paired bootstrap intervals. Hash all checkpoints. Do not promote synthetic proxy demonstrations as neural results. Freeze preregistered configurations and reserve genuinely held-out maps.

## Practical caveat
An unchanged full-map hash permits exact cache reuse, but on changed maps it forces global invalidation. Therefore speedups, if any, will likely be restricted to repeated exact-map queries. Neural predictions of changed local obstacle features must not be served from stale map keys.

## Result status
No new result table is asserted by this document. The included pilot runner is an instrumented starting point, not E1–E8 completion.
