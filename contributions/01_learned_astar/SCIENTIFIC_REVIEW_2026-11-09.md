# C01 — Scientific and reproducibility review (2026-11-09)

**Scope:** Contribution 01 source, retained historical metrics, official LILocBench
real-map offline pilot, ROS planning-only adapter, and readiness for instrumented
physical-robot experimentation. This is a targeted source and result audit, not
a certification of hardware safety or a full independent replication of the
historical 400-task synthetic experiment.

## 1. Research hypothesis and the actual paper

The C01 hypothesis is that a learned cost-to-go heuristic may reduce A*
expansions while maintaining acceptable solution quality. This is **distinct**
from the publication-facing DynNav-R C00 hypothesis in
`paper/dynnav_r/main.tex`: the information lost when executed
action-triggered topology-hazard history is collapsed to a state-only model.

The manuscript's 96-scenario comparison and Gazebo mechanism evidence do
not establish C01 effectiveness. The C01 offline real-map result must not be
inserted into that paper as hardware evidence or as support for its core claim.

## 2. Important findings

### A. Real-map pilot was completed but is not a physical-robot experiment

The official LILocBench map was parsed successfully in
[GitHub Actions run 42681341639](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42681341639);
the retained `.pt` checkpoint loaded without fallback. The map is a measured
physical-world occupancy map; the five route queries were **generated** on its
static free-space graph, not executed by the Dingo.

Five paired task means: Manhattan expansions 12,648.8 vs raw learned 14,740.8;
Manhattan latency 59.19 ms vs raw learned 975.74 ms. The raw neural method
expanded 16.5% more nodes and took roughly 16.5 times longer in this
small pilot. Preserve this **negative finding**. No generalization claim is
supported by a single map and five tasks.

### B. Checkpoint loading must be explicit

The generic `LearnedHeuristicWrapper` retains
`allow_missing_model=True` for historical demo compatibility. It can
substitute Manhattan when the saved checkpoint is absent. This is
**not acceptable** for research evaluation of a learned planner.

The C01 offline ROS-map study already has
`allow_missing_model=False`; the scientific statistical benchmark and
admissibility audit have now also been configured to use the C01-local
`models/heuristic_net_rich.pt` by default and refuse missing-model fallback.

Do not reclassify earlier historical CSVs as strict checkpoint-verified runs
without their recorded environment, model identity, logs and hashes.

### C. Raw heuristic does not have an optimality proof

The original A* keeps a closed set without reopening on improved paths.
The raw network heuristic is not known to be admissible or consistent, so
there is no global optimality guarantee. The Manhattan-clipped heuristic is
admissible on a four-connected unit-cost grid, but may be inconsistent;
the generic closed-list A* should be studied for reopen behavior before
stronger clipped-optimality statements under arbitrary learned predictions.

The `code/ergo_optimal.py` prototype deliberately keeps **Manhattan**
as the primary A* priority and permits neural predictions only as
tie-breakers, making its guarantee narrower and clearer. This is not a
proof for dynamic maps, kinodynamic constraints or robot actuator safety.

### D. Training provenance and data separation are unresolved

The saved `heuristic_net_rich.pt` is a real model state dictionary that
was loaded during the map pilot. Nevertheless, the repository's
`code/train_heuristic_from_npz.py` trains on the supplied `.npz`
features without a documented held-out train/validation/test topology split.
It saves a raw `state_dict` without a metadata bundle linking exact
dataset SHA, training seed, optimizer, feature schema and independent
evaluation maps. The original dataset provenance and overlap with held-out
tasks are not independently verified.

A separate `code/train_heuristic.py` uses a **4-feature** input model, unlike
the **11-feature** C01 rich heuristic; these are separate historical paths,
not evidence that the rich checkpoint was trained by the 4-feature script.
`code/train_heuristic_demo.py` can generate **dummy synthetic samples** and
must not be presented as physical-world training.

**Required next model study:** freeze multiple map-level train/validation/test
splits, record data/checkpoint hashes and training runs, compare against
Manhattan/zero baselines and report held-out error, admissibility and runtime.

### E. Historical timing script mixes contribution boundaries

`experiments/timing_benchmark.py` imports
`info_gain_planner` and `multiobj_planner`, benchmarks entropy/uncertainty
and Pareto-front calculations, and does **not** directly time the C01
learned A* search. Preserve it for historical context but do not use its
`timing_results.csv` as evidence of C01 neural A* speed.

### F. ROS interface is present, physical integration is not

`experiments/ros2_get_plan_node.py` provides a **planning-only** ROS 2
`GetPlan` service and publishes C01 diagnostics; it does not publish
`/cmd_vel` and is not automatically installed as a Nav2 GlobalPlanner.
Pure Python grid-geometry tests are available.

A real C01 physical validation requires selecting the actual robot,
a reviewed C01/Nav2 controller integration, operator-supervised safety
commissioning, synchronized physical logs and independently checked
matched trials. No physical C01 experiments were performed in this review.

## 3. Evidence maturity matrix

| Category | C01 evidence on 2026-11-09 |
|---|---|
| Historical synthetic search benchmark | Retained results; strict reproducibility review still needed |
| Saved neural model | Present and loaded in actual offline map workflow |
| Neural training provenance / held-out map generalization | **Not verified** |
| Official recorded occupancy map | **Verified offline** |
| Five generated paired real-map route queries | **Executed; negative learned efficiency result** |
| ROS 2 plan-service code | **Implemented; runtime ROS service untested** |
| Nav2 global planner plugin for C01 | **Not implemented/verified** |
| Gazebo closed-loop C01 | **Not verified** |
| Physical C01 robot trajectory, rosbag and outcomes | **Not available; zero verified trials** |
| Hardware safety certification | **Not claimed** |
| Manuscript C00 representation claim validation | **Not established by C01** |

## 4. Reproduction and follow-up

Run from the repository root in the supported Python environment:

```bash
python -m pytest -q contributions/01_learned_astar/tests
python contributions/01_learned_astar/experiments/statistical_validation.py \
  --grid-size 40 --trials-per-density 100 --min-distance 20
python contributions/01_learned_astar/experiments/admissibility_audit.py
```

The last two commands need the saved C01 checkpoint and PyTorch. They are
listed for reproduction; this source review does **not** claim that the
full 400-task benchmark or all-state audit were rerun at this commit.

See [REAL_DATA_PROTOCOL.md](REAL_DATA_PROTOCOL.md),
[REAL_ROBOT_README.md](REAL_ROBOT_README.md),
[ROS2_PLANNING_INTERFACE.md](ROS2_PLANNING_INTERFACE.md) and
[PHYSICAL_ROBOT_PROTOCOL.md](PHYSICAL_ROBOT_PROTOCOL.md).

**Conclusion:** C01 is a substantive research prototype with executed
real-map offline evaluation and meaningful negative results. It is **not**
yet validated on a physical robot; no scientifically defensible statement
can convert source code, archived ROS data, or simulator results into a
physical C01 robot experiment.
