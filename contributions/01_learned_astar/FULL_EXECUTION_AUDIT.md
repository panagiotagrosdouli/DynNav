# C01 — Exhaustive file inventory and execution matrix

**Audit date:** 2026-11-09  
**Scope:** Every file under `contributions/01_learned_astar/`, not the entire DynNav repository.  
**Main research question:** Whether a learned heuristic is scientifically useful compared with classical optimal A*, without conflating engineered interfaces, prerecorded robotics data and physical robot experiments.

## Executed source-of-truth evidence

The dedicated [C01 full-file audit workflow](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42697927252) **completed successfully** on source commit `0bbf19221d4a9877926e228e370f709bcd85d3fb`.

The job performed an integrity check on **all 74 C01 files present on that revision**, recorded SHA-256 for each file, ran all C01 tests and actually executed representative legacy training and planner commands.

### Whole-directory file-by-file results

| File category | Number | Per-file integrity checks | What this DOES NOT prove |
|---|---:|---|---|
| Python source files | 37 | Parsed and compiled Python AST | That every optional entrypoint was executed to completion |
| Saved PyTorch checkpoints | 13 | Loaded each state dictionary; checked tensor shape and finite parameters | Original training provenance, real-world generalization, model quality |
| NPZ dataset | 1 | Loaded all arrays; verified finite numerical contents | Training/validation/test independence |
| Historical CSV results | 7 | Parsed headers and rows | That all historic numerical results were independently reproduced |
| PNG results | 3 | Image decode/verification | Scientific validity of figures |
| SVG research figure | 1 | XML/SVG parsing | Accuracy of illustrated hypothesis |
| Markdown documents | 12 | Readable, nonempty | Truth or completeness of all past scientific claims |
| **TOTAL** | **74** | **All files structurally passed** | Full physical robot validation |

The actual machine-readable JSON evidence artifact is `results/c01_full_audit/all_files.json` in the workflow artifact `c01-every-file-and-execution-matrix`. Every record contains the relative path, size, SHA-256 and check status.

**Important:** This matrix intentionally distinguishes `SOURCE_COMPILES_RUNTIME_NOT_FULLY_EXECUTED`, `CHECKPOINT_STRUCTURALLY_VERIFIED_NOT_EFFICACY_VALIDATED` and `DOCUMENT_READABLE_NOT_FACT_INDEPENDENTLY_VERIFIED`. A green structural report alone never means all code paths or scientific claims work.

### Actually executed tests and experiments

The workflow passed **30 C01 pytest tests**, including the previously existing C01 ERGO tests and newer ROS2 grid/metadata/hardware-claim tests plus new model-width and complete-inventory regressions.

Experiments actually run with the retained real checkpoint:

- The original `experiments/eval_astar_learned.py` (four controlled synthetic tasks).
- `experiments/statistical_validation.py` (small seeded randomized grid pilot).
- `experiments/admissibility_audit.py` (small exact-cost sampled audit).
- `experiments/ergo_pilot.py` (two map-cache/budget episodes).
- The historical `code/astar_learned_heuristic.py` demo with original checkpoint and a new logged NPZ, executed in an isolated temporary working directory.
- `results/autotune_heuristic.py` with one actual fine-tuning iteration, operating strictly on a copy of the retained original checkpoint.
- The historically mislocated `experiments/timing_benchmark.py`, using its real external C07 information-gain and `core/multiobj_planner.py` dependencies but synthetic temporary coverage fixtures. Its reported timings are **NOT** C01 A* timings.

Legacy training paths actually executed with short, explicitly **synthetic-only** 4-feature dataset fixtures:

- `code/train_heuristic.py` (one epoch).
- `code/train_heuristic_ablation.py` (one epoch each, hidden=32 and hidden=128).
- `code/train_heuristic_data_sweep.py` (one epoch for 50% dataset fraction).
- `code/train_heuristic_curriculum.py` (one epoch for each 8/16/32 stage).
- `code/train_heuristic_uncertainty.py` (legacy 40-epoch loop on 32 synthetic samples).
- `code/train_heuristic_demo.py` (one epoch on generated dummy CSV).
- `code/train_heuristic_from_npz.py` (one epoch on retained `models/heuristic_logs.npz`; not held-out training validation).

All newly produced models were checked for finite state tensors. The preserved original C01 checkpoint was confirmed unchanged after online fine-tuning by SHA-256:
`640ec68fcf1a04b3fc3abbc146ff5aaaee58a5a170ec5770c39459cce972b19a`.

### Confirmed defects repaired

1. **Incorrect historical model hidden widths:** `code/learned_heuristic.py` ignored explicit `hidden=32` / `hidden=128` when `hidden_dim` used its default 64. It now implements the requested hidden width and rejects conflicting explicit widths. Tests assert actual checkpoint matrix dimensions.
2. **Silent fallback masking learned evaluation:** `experiments/statistical_validation.py` and `experiments/admissibility_audit.py` now require a valid neural checkpoint in clipped mode, instead of silently substituting Manhattan.
3. **Autotune could not reliably be run from the repository root and modified the input model:** `results/autotune_heuristic.py` now resolves actual code/core dependencies and copies the original checkpoint into an isolated output before fine-tuning.
4. **Misleading broken historical timing entrypoint:** `experiments/timing_benchmark.py` now resolves actual NBV and multiobjective imports, accepts explicit input paths and labels its results as historical C07/multiobjective timing, not learned A* performance.

### Still distinct from real robot hardware results

Earlier evidence already executed in the repository:

- Actual LILocBench real map + C01 checkpoint offline planning.
- Decoding 25,920 genuine recorded Clearpath Dingo messages.
- Conversion/replay of recorded Dingo ROS1 data into ROS2 Jazzy.
- ROS2 C01 `GetPlan` on authentic office occupancy geometry.
- ROS2 closed-loop simulated differential-drive path following in all three C01 variants.

**None of the above establishes that a real Dingo physically executed C01**. Hardware-controlled navigation remains zero verified trials. The ROS2 closed-loop simulated plant is not Gazebo physics or a physical platform. Consult `ROS2_CLOSED_LOOP_EVIDENCE.md` and `REAL_ROBOT_README.md`.

### Remaining independent research validation

- Independently reconstruct the training data origin and map-level held-out split for each saved checkpoint.
- Execute a larger number of independently recorded occupancy maps with preregistered paired planning tasks and confidence intervals.
- Audit all legacy output tables against source commands and input hashes; structure checks are not historical replication.
- Establish and test a reviewed, platform-specific **Nav2 closed-loop integration** for C01, distinct from the generic C00 plugin.
- Require a connected actual robot and onsite trained safety operator, functioning independent E-stop and authenticated physical ROS2 bag before publishing physical navigation claims.
- Do not describe the historical multiobjective planning script as learned-A* evidence.
- In the latest C01 audit job, raw missing-optional-dependency script cases may remain outside full runtime coverage; the file-level JSON explicitly preserves that limitation.

**Verdict:** All inventoried files passed *structural* inspection, C01 existing tests and broad executable pilot coverage passed, and confirmed engineering defects were corrected. This is not a claim that every historical experiment was fully reproduced or that C01 drove a real robot.
