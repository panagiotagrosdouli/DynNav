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
