# C07 — Actual LILocBench office geometry, synthetic frontier sensing and independent NBV audit

**Execution evidence:** [GitHub Actions #42780371125](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42780371125) **passed**. Source map: the original official LILocBench 1000×1000 ROS occupancy grid (0.05 m/cell), with archive and map hashes independently checked.

## Actual experiment

The original physical-world geometry was loaded but four partial maps were **generated computationally**, by revealing cells within an ideal 24-cell circle around geographically separated starts. A reachable 4-connected free-space frontier was identified in each synthetic observation, candidate views were sampled reproducibly, and two actual C07 view-scoring methods were applied: classic ideal unknown-gain/travel-distance and the existing risk/returnability-aware `score_candidates()`. Risk is a heuristic *known-obstacle proximity*, not calibrated collision probability. Connectivity is a fixed constant and therefore contains **no radio evidence**. Neither a physical camera/LiDAR sensor nor any actual C07 robot exploration was active.

The first successful pilot run #42779990154 selected all four initial starts within the same open area; the policies agreed on all selected views. Its scientific information was limited. We therefore replaced uniform closely clustered start selection with spatial separation across connected real-map geometry. The subsequent successful run #42780371125 produced:

| Trial | Start cell (x,y) | Evaluated frontiers | Selected views equal? | Classic estimated unknown pixels | Safe estimated unknown pixels | Classic obstacle proximity proxy | Safe obstacle proximity proxy |
|---|---|---:|---|---:|---:|---:|---:|
| 0 | (370,489) | 100 | No | 403 | 375 | 0.043977 | 0.003279 |
| 1 | (494,371) | 100 | Yes | 403 | 403 | 0.000835 | 0.000835 |
| 2 | (422,479) | 93 | No | 403 | 403 | 0.039514 | 0.001984 |
| 3 | (537,477) | 68 | Yes | 403 | 403 | 0.028413 | 0.028413 |

The C07 score differs from classic in **2 of 4** controlled scenarios; in these cases the selected target had a lower **analytic proximity proxy**, in one case with lower idealized unknown-cell gain. This is a demonstration of code behavior, not a statistically powered improvement.

**Important negative/neutral result:** The simple `1/(1+known_return_distance/30)` returnability proxy was **identical, 0.555556, at the selected viewpoints in all four cases**. Hence the present experiments **do not establish that returnability weighting adds discriminating information** beyond distance and obstacle proximity. To test the actual hypothesis, future candidate sets must vary known-map return distances and real return-path feasibility. The 2/4 selection differences cannot be attributed causally to returnability.

## Provenance and reproducibility

Source map image SHA-256: `8a9ff6aa0d954e7743ed7dd1801d9df2a44a4d023cfda8de6ef12daa39cd57bf`.

```bash
python contributions/07_next_best_view/experiments/eval_real_office_partial_observation_nbv.py \
  /path/to/official/map_office.yaml \
  --output-dir results/c07_real_office --starts 4 --seed 17 \
  --observed-radius 24 --sensor-radius 15
```

CI source: `.github/workflows/c07-real-office-nbv.yml`. The workflow artifact `c07-real-office-synthetic-observation-frontier-nbv` contains full individual viewpoint rows, actual scored comparisons `paired_rankings.csv` and immutable map/experiment provenance.

### Engineering verification

New tests explicitly change hidden occupancy outside the synthetic observation radius and confirm **exactly identical frontier scores and ranked candidates**. They also verify that scored frontier cells remain reachable via the known-free-space BFS, that invalid origins fail and that actual unknown cells cannot silently be treated as known obstacles. All tests ran in the passing CI job.

The historical `contributions/07_nbv_exploration/` is part of the SAME C07 research contribution; this canonical study resides in `contributions/07_next_best_view/` and does not purport to execute every historical NBV script.

### Scientific limitations

- Real static **map geometry**, synthetic ideal circular sensing and synthetic exploration viewpoints; no line-of-sight occlusion, range errors, 3D perception, actual LiDAR/FOV, localization uncertainty or map updates.
- Unknown footprint count is **not entropy reduction**, actual observed information gain or trained mutual information.
- Obstacle proximity is **not measured collision risk**.
- The constant connectivity bonus is not a real RSSI/SNR estimate.
- Candidate returnability is only a monotonic function of known-grid path distance to the base; no dynamic loss of escape options.
- No robot motion, actual ROS2 mission, physical C07 exploration or physical safety outcome. **Verified physical C07 trials: 0.**

**Conclusion:** Real-office-map algorithms and test scaffolding operate correctly and expose concrete policy-selection differences without using hidden map occupancy to score future actions. No significant NBV performance or physical exploration benefit has been demonstrated yet.
