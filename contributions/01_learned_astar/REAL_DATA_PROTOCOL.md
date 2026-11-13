# C01 — official LILocBench occupancy-map evaluation protocol

**Status:** executable real-map offline evaluation protocol. The presence of this
script/workflow is not itself evidence of a successful real-data experiment.
See the corresponding CI job and generated artifact for execution status.

## Scientific question

Given an independently measured occupancy grid, does the existing C01 neural
heuristic reduce A* search expansions for generated, reachable map queries, and
what is the wall-clock cost of neural inference compared with optimal Manhattan A*?

The map is from LILocBench, whose recordings were acquired using a Clearpath
Dingo in an office setting. **The map is real; the start/goal queries are
generated on that static map.** The recorded robot did not execute these
alternative paths. The experiment does not reconstruct moving people from the
occupancy grid or demonstrate dynamic replanning.

## Map source and license

Official dataset: https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/

Official map archive:
https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/data/map_office.zip

Trekel et al., *Benchmark for Evaluating Long-Term Localization in Indoor
Environments Under Substantial Static and Dynamic Scene Changes*, IROS 2025.

Dataset license: **CC BY-NC-SA 4.0**. Respect attribution and non-commercial
share-alike restrictions for redistributed adaptations. Do not commit the raw
map archive or extracted dataset files.

## Reproduction

Download/extract the original map ZIP. Supply its ROS `.yaml` file (referencing
the image alongside it).

Run the baseline-only geometry and path-quality checks:

```bash
python -m pip install -e ".[dev]"
python contributions/01_learned_astar/experiments/eval_real_ros_map.py \
  /path/to/map.yaml --output-dir results/c01_lilocbench_real_map/baselines \
  --n-tasks 8 --seed 17 --min-distance 8
```

Run the **actual saved neural checkpoint**, requiring PyTorch and failing loudly
if it cannot be loaded:

```bash
python contributions/01_learned_astar/experiments/eval_real_ros_map.py \
  /path/to/map.yaml \
  --model contributions/01_learned_astar/models/heuristic_net_rich.pt \
  --output-dir results/c01_lilocbench_real_map/neural \
  --n-tasks 5 --seed 17 --min-distance 8
```

The GitHub workflow `.github/workflows/c01-real-ros-map.yml` downloads the
official 17.4 KB map archive independently, runs fixture tests, checks map
geometry, executes both experiments and retains their output artifacts.

## Implementation and validity boundaries

- Uses the existing `dynnav.mapping.ros_map.load_ros_map` parser, retaining
  original image-axis convention, ROS map origin and occupancy thresholds.
- Unknown cells are blocked conservatively; four-connected, unit-step paths.
- Selects pairs from a common connected free-space component. All methods use
  identical queries and the map is unchanged between methods.
- Compares `astar_manhattan`, `dijkstra_h0`, `learned_raw`, and
  `learned_manhattan_clipped` (if the checkpoint is supplied and loaded).
- Validates every returned path against connectivity, obstacles and endpoints.
- Checks that zero and clipped heuristics match the Manhattan reference cost.
- The raw learned mode is **not guaranteed admissible**, and this closed-list
  implementation does not reopen nodes. Path-cost equality is empirical only.
- Model initialization is timed separately from search, with a single warm
  checkpoint instance reused across the generated queries.
- Dataset/map and neural model SHA-256 are retained in `summary.json`;
  per-query rows are in `trials.csv`.
- One occupancy map does not establish generalization. Tests across multiple
  independent maps and train/test leakage checks remain necessary.
- Timing depends on the GitHub runner hardware and background load; small
  samples are descriptive, not definitive speed benchmarks.
- A real map does **not** imply real robot navigation by DynNav, dynamic obstacle
  tracking, or real-world action-triggered topology-hazard efficacy.

## Acceptance criteria

Do not claim success unless the real-map workflow completes and its retained
`summary.json` shows `neural_model_loaded: true` for the neural run. Verify
all nonempty trial rows, unchanged map hashes between runs, model hash,
path-cost gaps, expansion measurements, and workflow logs. If unavailable,
classify the real-map neural result as blocked or partial, not passed.

## First completed official-map execution — 2026-11-09

**Verified CI source:** [C01 official-map workflow #42681341639](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42681341639) on the PR's original source commit `dfed1b25bbb4d20ff95bd9e00e6ab99b13ed85bb`. The workflow completed successfully, including its four fixture tests, upstream download, 8-task baseline-only study, 5-task four-method study, and uploaded a research artifact named `c01-lilocbench-official-real-map-evaluation`. These are **offline generated-queries-on-real-map** results, not executed robot paths.

### Verified dataset geometry and provenance

- Official map archive: `map_office.zip` from the LILocBench institutional dataset page.
- Archive SHA-256: `941f96bf90d7d89dddf76fb4864f45212318d39f2b4f1220318786e53f48f6b0`.
- Map image SHA-256: `8a9ff6aa0d954e7743ed7dd1801d9df2a44a4d023cfda8de6ef12daa39cd57bf`.
- Map YAML SHA-256: `6e61ed85520c2e4638684734c738daf63c17de830a535cd8458cee14cd1fb11e`.
- Grid: **1000 × 1000** cells at **0.05 m/cell**, origin **(-25.0, -25.0, 0.0)**.
- Under unknown-as-blocked, **894,999 blocked/unknown cells**, and **243** distinct connected free components.
- Saved neural model SHA-256: `640ec68fcf1a04b3fc3abbc146ff5aaaee58a5a170ec5770c39459cce972b19a`; neural model actually loaded without fallback.
- All query paths were checked for four-connectivity, free occupancy and exact endpoints.

### Baseline-only study (8 queries, seed 17)

| Method | Mean expanded nodes | Mean path cost (cells) | Mean measured search time |
|---|---:|---:|---:|
| Manhattan A* | 13,348.375 | 292.5 | 60.661 ms |
| Dijkstra (h=0) | 37,990.5 | 292.5 | 171.260 ms |

### Four-method study (5 paired queries, seed 17)

| Method | Mean expanded nodes | Mean path cost (cells) | Mean measured search time | Tasks suboptimal vs Manhattan |
|---|---:|---:|---:|---:|
| Manhattan A* | 12,648.8 | 286.2 | 59.190 ms | 0 |
| Dijkstra (h=0) | 33,726.0 | 286.2 | 154.725 ms | 0 |
| Learned raw | 14,740.8 | 286.2 | 975.738 ms | 0 |
| Learned Manhattan-clipped | 15,082.2 | 286.2 | 1,010.293 ms | 0 |

On these five tasks, the raw learned planner expanded **16.5% more nodes** and took **16.5×** as long in the measured warm-search interval compared with Manhattan A*. The clipped learned planner expanded **19.2% more nodes** and took **17.1×** as long.

**Interpretation:** The real-map pilot provides no evidence of learned-search efficiency improvement on this particular map and these five generated queries. All measured path costs happened to match; this does **not** prove global admissibility or universal optimality of the raw neural heuristic. The sample is deliberately small; timings are GitHub-hosted-runner-specific. Additional independent maps, held-out topologies, checkpoint training provenance, larger paired task sets and run-to-run timing distributions are required for generalization claims.

The source dataset does **not** establish physical execution, action-triggered changes, or the performance of a trained learned model on sensor data beyond the measured map queries.

**Artifact:** Inspect/download the workflow artifact from the linked run for `baselines/trials.csv`, `baselines/summary.json`, `neural/trials.csv`, `neural/summary.json`. Keep the original dataset out of Git.
