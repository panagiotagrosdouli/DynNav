# Full repository folder-topology audit — 2026-11-09

> **Immutable GitHub tree snapshot:** `b626d6e9b5bf8b8cf1ec87906597d767224f5f37` (`main`).
> The Git Trees API returned `truncated=false`. This is a **complete tracked-path inventory**, not a claim that every file was read line by line or that every module passed runtime tests. Git does not track empty folders, so untracked and empty local directories are outside this inventory.

## Scope and counts

- Root-level tracked directories: **50**
- All tracked directory entries, including root-level entries: **381**
- Tracked files: **2086**
- Total recursive tree entries: **2467**
- Folder inventory grouped by the root-level owner is reproduced **verbatim** below.

## Root directory responsibility matrix

| Root | Tracked folder paths | Tracked files | Observed/provisional role |
|---|---:|---:|---|
| `.github/` | 3 | 20 | GitHub Actions and issue templates |
| `.streamlit/` | 1 | 1 | Streamlit configuration |
| `_misc/` | 1 | 3 | Legacy miscellaneous assets |
| `analysis/` | 1 | 40 | Scientific analysis scripts/notebooks |
| `app/` | 2 | 16 | Streamlit app and pages |
| `apps/` | 6 | 14 | FastAPI entrypoint and Next.js Researcher frontend |
| `assets/` | 4 | 30 | Media and style assets |
| `benchmarks/` | 6 | 40 | Older benchmark families |
| `code_scripts/` | 1 | 1 | Legacy standalone scripts |
| `configs/` | 2 | 18 | Runtime and contribution registries |
| `contributions/` | 144 | 677 | C01–C26, C27, and shared exploratory code |
| `core/` | 1 | 26 | Historical planning/control modules |
| `cpp_extension/` | 1 | 4 | Older C++/Python integration |
| `cybersecurity_ros2/` | 2 | 11 | Security-related ROS prototypes |
| `data/` | 2 | 3 | Local data and plots |
| `data_curriculum/` | 1 | 3 | Curriculum fixtures |
| `datasets/` | 1 | 9 | Dataset helpers/metadata |
| `debug/` | 2 | 1 | Debug artifacts |
| `docs/` | 2 | 66 | Documentation and historical archives |
| `dynnav/` | 13 | 96 | Canonical Python package and planner implementations |
| `figures/` | 1 | 5 | Scientific figures |
| `generators/` | 1 | 14 | Scenario/data generators |
| `ig_explorer/` | 4 | 8 | Information-gain exploration package |
| `launch/` | 1 | 2 | Legacy launch files |
| `logs_ablation/` | 1 | 2 | Retained ablation logs |
| `logs_benchmark/` | 1 | 4 | Retained benchmark logs |
| `logs_calibration/` | 1 | 7 | Retained calibration logs |
| `logs_calibration_ensemble/` | 1 | 6 | Retained ensemble calibration logs |
| `logs_ood/` | 1 | 4 | Retained OOD logs |
| `logs_real_world/` | 1 | 6 | Real-world-labelled logs: provenance requires individual verification |
| `modules/` | 20 | 71 | Exploratory sensing/control/planning modules |
| `nav_research/` | 3 | 18 | Legacy ROS-oriented research code |
| `neural_uncertainty/` | 9 | 74 | Neural uncertainty research artifacts |
| `paper/` | 2 | 26 | Manuscript and scientific evidence manifest |
| `pdfs/` | 1 | 26 | PDF artifacts |
| `photogrammetry_module/` | 3 | 6 | Photogrammetry experiments |
| `research_experiments/` | 9 | 83 | Additional experiments |
| `research_results/` | 1 | 1 | Research-result artifacts |
| `resource/` | 1 | 2 | ROS package resources |
| `results/` | 18 | 167 | Retained research outputs and manifests |
| `ros2/` | 1 | 1 | ROS-related support |
| `ros2_ws/` | 82 | 174 | ROS 2 Jazzy/Nav2 source tree and benchmark packages |
| `scripts/` | 2 | 58 | Executable analysis/benchmark/reproducibility scripts |
| `src/` | 8 | 46 | Dashboard and compatibility source |
| `test/` | 1 | 3 | Legacy tests |
| `tests/` | 2 | 105 | Canonical Python test suite |
| `tools/` | 1 | 7 | Support utilities |
| `utils/` | 1 | 29 | Legacy shared utilities |
| `vercel_app/` | 3 | 9 | Standalone Next.js Vercel frontend |
| `website/` | 4 | 12 | Public Next.js research website |

Roles are an initial classification based on paths, packaging, workflow configuration, and the existing `docs/REPOSITORY_GUIDE.md`. They are **not** claims that every file within a directory was semantically reviewed or validated.

## Confirmed canonical paths and integration edges

| Capability | Source or adapter | Interface/evidence |
|---|---|---|
| Python research package | `dynnav/` | `pyproject.toml` wheel setting, `dynnav/__init__.py`, CI canonical-package assertion |
| Action-triggered hazard model | `dynnav/commitment_hazard.py` | `dynnav/recoverability_belief.py`; `dynnav/planners/` |
| Research experiment runners | `scripts/run_*.py` and `dynnav/experiments/` | `configs/`, `results/`, paper evidence manifest |
| Registered numbered tracks | `contributions/` | `configs/contributions/registry.yaml` and `experiments.yaml`; C01–C26 smoke suite |
| Theory track | `contributions/27_Recoverability_Theory/` | Not part of the C01–C26 executable registry |
| ROS 2/Nav2 C++ adapter | `ros2_ws/src/dynnav_nav2_cpp/` | Jazzy CI plugin build and tests |
| ROS/Gazebo benchmark support | `ros2_ws/src/dynnav_nav2_benchmark/` | Dedicated scenario/benchmark workflows; evidence scopes must be checked individually |
| Research API | `apps/api/main.py` → `dynnav.researcher.api` | FastAPI `/health`, `/v1/capabilities`, protocol/experiment routes |
| Researcher frontend | `apps/web/` | `NEXT_PUBLIC_DYNNAV_API_URL`, with localhost development default; needs running API |
| Public portal | `website/` | Static Next.js page and C01–C26 explorer; `scripts/build_web_portal.sh` |
| GitHub Pages combined site | `website/` + `apps/web/` | `.github/workflows/web-portal.yml`: `.web-dist/` and `/researcher` |
| Standalone Vercel frontend | `vercel_app/` | Separate Next.js build; production project/deployment must be verified independently |
| Streamlit laboratory | `app/` | `.streamlit/`; ROS map and dashboard components |
| Scientific publication | `paper/dynnav_r/` | `paper/dynnav_r/evidence_manifest.json`, `CLAIM_EVIDENCE_MATRIX.md` |
| Canonical Python regression | `tests/` | `.github/workflows/ci.yml`: pytest across Python 3.10–3.12 |

## Overlap and historical-compatibility watchlist

These overlaps are **candidates for investigation**, not proven duplicate or dead code.

1. **`dynnav/` vs `src/dynnav/` vs `core/` vs `modules/`:** The canonical import resolves to the root `dynnav/`, verified by the CI job. `src/dynnav/` contains a README instead of a Python package at this snapshot. Do not reorganize legacy `core/` or `modules/` without import/call-site and equivalence checks.
2. **`contributions/07_nbv_exploration/` and `contributions/07_next_best_view/`:** One C07 research track, historically split into two folders. Preserve both until dependency, API and experiment migration is reviewed.
3. **`app/`, `apps/web/`, `website/`, `vercel_app/`:** Different interfaces (Streamlit, Next.js researcher, public portal, standalone Vercel). Shared branding does not make these implementation duplicates.
4. **`apps/api/` and `dynnav/researcher/`:** The former is a thin ASGI entrypoint; the latter owns FastAPI routes and experimental service logic. Avoid creating an unrelated second API.
5. **`tests/` vs `test/` vs `contributions/tests/`:** Verify discovery, path-specific runners and independence before moving tests.
6. **`results/` vs `research_results/` vs `logs_*/`:** Investigate provenance and manifest references before archiving. Folder names alone do not certify data provenance.
7. **`docs/SYSTEM_ARCHITECTURE.md`:** Earlier references to `src/dynnav/` as the package are historical. The canonical location is `dynnav/`; update the architecture entrypoint without changing algorithms.
8. **`docs/CONTRIBUTION_FEATURE_CATALOG.md`:** The older C11 "Twin-Critic Reinforcement Learning" label conflicts with the current registered C11 VLM Navigation Agent.
9. **`nav_research/`, `launch/`, `resource/`, `ros2_ws/`:** Distinguish legacy ament package entrypoints from the verified Jazzy Nav2 workspace before consolidating launch files.

## Executed validation already visible on GitHub

The following **GitHub-hosted CI runs** were completed successfully for snapshot SHA `b626d6e9b5bf8b8cf1ec87906597d767224f5f37`:

| Check | Run ID | Result | Evidence scope |
|---|---:|---|---|
| CI | [42625621006](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42625621006) | success | Python 3.10–3.12, Nav2 plugin checks, website/researcher builds, markdown |
| C01–C26 experiment suite | [42625621066](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42625621066) | success | Deterministic registered smoke suite; not real-robot evidence |
| Streamlit Dashboard | [42625621101](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42625621101) | success | Streamlit workflow checks |
| Web portal | [42625621027](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42625621027) | success | Build/typecheck and portal artifact |
| Documentation integrity | [42625621047](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42625621047) | success | Documentation workflow contract |
| Pages build and deployment | [42625619018](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42625619018) | success | GitHub Pages workflow success; not an independent manual browser audit |

**Execution caveat:** These were GitHub Actions results inspected through the GitHub integration, not tests rerun locally by the author of this snapshot.

## Recommended non-destructive follow-through

1. Inspect tracked imports, scripts and launch references before promoting any historical module as canonical.
2. Generate and review an import/dependency graph from a clean checkout, recording unresolved/optional imports separately.
3. Add smoke tests for important actual integrations, especially researcher API → frontend, where service availability can be controlled.
4. Confirm actual deployed website links, backend CORS, health, and runtime API access; a static `/researcher` page may load even while the API is absent.
5. Preserve dataset provenance and research-claim boundaries. CI successes and the LILocBench trajectory summary are not planner-comparison or physical-hardware evidence.
6. Do **not** move or remove legacy paths solely to make the tree visually smaller.

## Complete tracked directory-path inventory (381 paths)

### `.github/` (3 folder paths)

```text
.github
.github/ISSUE_TEMPLATE
.github/workflows
```

### `.streamlit/` (1 folder paths)

```text
.streamlit
```

### `_misc/` (1 folder paths)

```text
_misc
```

### `analysis/` (1 folder paths)

```text
analysis
```

### `app/` (2 folder paths)

```text
app
app/pages
```

### `apps/` (6 folder paths)

```text
apps
apps/api
apps/web
apps/web/app
apps/web/components
apps/web/lib
```

### `assets/` (4 folder paths)

```text
assets
assets/contributions
assets/readme
assets/styleguide
```

### `benchmarks/` (6 folder paths)

```text
benchmarks
benchmarks/dynamic_self_aware_astar
benchmarks/fragile_commitment
benchmarks/fragile_commitment/configs
benchmarks/self_aware_astar
benchmarks/self_aware_navigation
```

### `code_scripts/` (1 folder paths)

```text
code_scripts
```

### `configs/` (2 folder paths)

```text
configs
configs/contributions
```

### `contributions/` (144 folder paths)

```text
contributions
contributions/01_learned_astar
contributions/01_learned_astar/assets
contributions/01_learned_astar/code
contributions/01_learned_astar/docs
contributions/01_learned_astar/experiments
contributions/01_learned_astar/models
contributions/01_learned_astar/results
contributions/01_learned_astar/tests
contributions/02_uncertainty_calibration
contributions/02_uncertainty_calibration/assets
contributions/02_uncertainty_calibration/code
contributions/02_uncertainty_calibration/docs
contributions/02_uncertainty_calibration/experiments
contributions/02_uncertainty_calibration/models
contributions/02_uncertainty_calibration/results
contributions/02_uncertainty_calibration/results/uncertainty_plots
contributions/03_belief_risk_planning
contributions/03_belief_risk_planning/assets
contributions/03_belief_risk_planning/code
contributions/03_belief_risk_planning/docs
contributions/03_belief_risk_planning/experiments
contributions/03_belief_risk_planning/results
contributions/04_irreversibility_returnability
contributions/04_irreversibility_returnability/assets
contributions/04_irreversibility_returnability/code
contributions/04_irreversibility_returnability/docs
contributions/04_irreversibility_returnability/experiments
contributions/04_irreversibility_returnability/results
contributions/04_irreversibility_returnability/tests
contributions/05_safe_mode_navigation
contributions/05_safe_mode_navigation/assets
contributions/05_safe_mode_navigation/code
contributions/05_safe_mode_navigation/docs
contributions/05_safe_mode_navigation/experiments
contributions/05_safe_mode_navigation/results
contributions/06_energy_connectivity
contributions/06_energy_connectivity/assets
contributions/06_energy_connectivity/code
contributions/06_energy_connectivity/docs
contributions/06_energy_connectivity/experiments
contributions/06_energy_connectivity/results
contributions/07_nbv_exploration
contributions/07_nbv_exploration/code
contributions/07_nbv_exploration/experiments
contributions/07_nbv_exploration/results
contributions/07_next_best_view
contributions/07_next_best_view/assets
contributions/07_next_best_view/code
contributions/07_next_best_view/docs
contributions/07_next_best_view/experiments
contributions/08_security_ids
contributions/08_security_ids/code
contributions/08_security_ids/docs
contributions/08_security_ids/experiments
contributions/08_security_ids/results
contributions/09_multi_robot
contributions/09_multi_robot/code
contributions/09_multi_robot/docs
contributions/09_multi_robot/experiments
contributions/09_multi_robot/results
contributions/10_human_language_ethics
contributions/10_human_language_ethics/code
contributions/10_human_language_ethics/demos
contributions/10_human_language_ethics/docs
contributions/10_human_language_ethics/experiments
contributions/10_human_language_ethics/results
contributions/11_vlm_navigation_agent
contributions/11_vlm_navigation_agent/docs
contributions/11_vlm_navigation_agent/experiments
contributions/11_vlm_navigation_agent/results
contributions/12_diffusion_occupancy
contributions/12_diffusion_occupancy/docs
contributions/12_diffusion_occupancy/experiments
contributions/13_latent_world_model
contributions/13_latent_world_model/docs
contributions/13_latent_world_model/experiments
contributions/14_causal_risk_attribution
contributions/14_causal_risk_attribution/docs
contributions/14_causal_risk_attribution/experiments
contributions/15_neuromorphic_sensing
contributions/15_neuromorphic_sensing/docs
contributions/15_neuromorphic_sensing/experiments
contributions/16_federated_nav_learning
contributions/16_federated_nav_learning/docs
contributions/16_federated_nav_learning/experiments
contributions/17_topological_semantic_maps
contributions/17_topological_semantic_maps/docs
contributions/17_topological_semantic_maps/experiments
contributions/18_formal_safety_shields
contributions/18_formal_safety_shields/docs
contributions/18_formal_safety_shields/experiments
contributions/19_llm_mission_planner
contributions/19_llm_mission_planner/docs
contributions/19_llm_mission_planner/experiments
contributions/20_multimodal_failure_explainer
contributions/20_multimodal_failure_explainer/docs
contributions/20_multimodal_failure_explainer/experiments
contributions/21_ppo_navigation_agent
contributions/21_ppo_navigation_agent/docs
contributions/21_ppo_navigation_agent/experiments
contributions/22_curriculum_rl
contributions/22_curriculum_rl/docs
contributions/22_curriculum_rl/experiments
contributions/23_gaussian_splatting_mapper
contributions/23_gaussian_splatting_mapper/docs
contributions/23_gaussian_splatting_mapper/experiments
contributions/24_nerf_uncertainty
contributions/24_nerf_uncertainty/docs
contributions/24_nerf_uncertainty/experiments
contributions/25_adversarial_attack_simulator
contributions/25_adversarial_attack_simulator/docs
contributions/25_adversarial_attack_simulator/experiments
contributions/26_swarm_consensus
contributions/26_swarm_consensus/docs
contributions/26_swarm_consensus/experiments
contributions/27_Recoverability_Theory
contributions/_unsorted
contributions/_unsorted/results
contributions/ablation_study
contributions/ablation_study/code
contributions/ablation_study/experiments
contributions/ablation_study/results
contributions/benchmarking
contributions/benchmarking/code
contributions/benchmarking/experiments
contributions/benchmarking/results
contributions/hybrid_learned_astar
contributions/hybrid_learned_astar/code
contributions/hybrid_learned_astar/experiments
contributions/hybrid_learned_astar/results
contributions/hybrid_planner
contributions/hybrid_planner/code
contributions/hybrid_planner/experiments
contributions/hybrid_planner/results
contributions/learned_uncertainty_astar
contributions/learned_uncertainty_astar/code
contributions/learned_uncertainty_astar/experiments
contributions/learned_uncertainty_astar/results
contributions/realtime_replanning
contributions/realtime_replanning/code
contributions/realtime_replanning/experiments
contributions/realtime_replanning/results
contributions/tests
```

### `core/` (1 folder paths)

```text
core
```

### `cpp_extension/` (1 folder paths)

```text
cpp_extension
```

### `cybersecurity_ros2/` (2 folder paths)

```text
cybersecurity_ros2
cybersecurity_ros2/nodes
```

### `data/` (2 folder paths)

```text
data
data/plots
```

### `data_curriculum/` (1 folder paths)

```text
data_curriculum
```

### `datasets/` (1 folder paths)

```text
datasets
```

### `debug/` (2 folder paths)

```text
debug
debug/artifacts
```

### `docs/` (2 folder paths)

```text
docs
docs/archive
```

### `dynnav/` (13 folder paths)

```text
dynnav
dynnav/contributions
dynnav/core
dynnav/evaluation
dynnav/experiments
dynnav/mapping
dynnav/planners
dynnav/prediction
dynnav/researcher
dynnav/safety
dynnav/security
dynnav/simulation
dynnav/uncertainty
```

### `figures/` (1 folder paths)

```text
figures
```

### `generators/` (1 folder paths)

```text
generators
```

### `ig_explorer/` (4 folder paths)

```text
ig_explorer
ig_explorer/ig_explorer
ig_explorer/resource
ig_explorer/test
```

### `launch/` (1 folder paths)

```text
launch
```

### `logs_ablation/` (1 folder paths)

```text
logs_ablation
```

### `logs_benchmark/` (1 folder paths)

```text
logs_benchmark
```

### `logs_calibration/` (1 folder paths)

```text
logs_calibration
```

### `logs_calibration_ensemble/` (1 folder paths)

```text
logs_calibration_ensemble
```

### `logs_ood/` (1 folder paths)

```text
logs_ood
```

### `logs_real_world/` (1 folder paths)

```text
logs_real_world
```

### `modules/` (20 folder paths)

```text
modules
modules/control
modules/costmap_monitor
modules/coverage_clustering
modules/drl_planner
modules/evaluation
modules/exploration
modules/fusion
modules/graph_planning
modules/mapping
modules/nce_monitor
modules/photogrammetry
modules/planning
modules/priority_mapping
modules/utils
modules/visual_odometry
modules/visualization
modules/vla
modules/vo_fusion
modules/vo_uncertainty
```

### `nav_research/` (3 folder paths)

```text
nav_research
nav_research/calib_active
nav_research/vla
```

### `neural_uncertainty/` (9 folder paths)

```text
neural_uncertainty
neural_uncertainty/results
neural_uncertainty/results/statistical_runs
neural_uncertainty/results/statistical_runs/full
neural_uncertainty/results/statistical_runs/no_coverage
neural_uncertainty/results/statistical_runs/no_online
neural_uncertainty/results/statistical_runs/no_priority
neural_uncertainty/results/statistical_runs/no_vla
neural_uncertainty/results/statistical_runs/no_vo_unc
```

### `paper/` (2 folder paths)

```text
paper
paper/dynnav_r
```

### `pdfs/` (1 folder paths)

```text
pdfs
```

### `photogrammetry_module/` (3 folder paths)

```text
photogrammetry_module
photogrammetry_module/code_scripts
photogrammetry_module/photogrammetry_module
```

### `research_experiments/` (9 folder paths)

```text
research_experiments
research_experiments/trust_aware_cvar
research_experiments/trust_aware_cvar/analysis
research_experiments/trust_aware_cvar/benchmark
research_experiments/trust_aware_cvar/core
research_experiments/trust_aware_cvar/figures
research_experiments/trust_aware_cvar/paper
research_experiments/trust_aware_cvar/results
research_experiments/trust_aware_cvar/results/tables
```

### `research_results/` (1 folder paths)

```text
research_results
```

### `resource/` (1 folder paths)

```text
resource
```

### `results/` (18 folder paths)

```text
results
results/fragile_commitment_v2
results/manifests
results/multiseed
results/noisy_activation
results/ros2_gazebo
results/ros2_gazebo/dynamic_run_31488640894
results/ros2_gazebo/dynamic_run_31488640894/behavior_trees
results/ros2_gazebo/static_run_31488640827
results/statistical_runs
results/statistical_runs/astar_classic
results/statistical_runs/astar_learned
results/statistical_runs/full
results/statistical_runs/no_coverage
results/statistical_runs/no_online
results/statistical_runs/no_priority
results/statistical_runs/no_vla
results/statistical_runs/no_vo_unc
```

### `ros2/` (1 folder paths)

```text
ros2
```

### `ros2_ws/` (82 folder paths)

```text
ros2_ws
ros2_ws/lidar_slam_tb3
ros2_ws/lidar_slam_tb3/src
ros2_ws/lidar_slam_tb3/src/dynamic_nav
ros2_ws/lidar_slam_tb3/src/dynamic_nav/config
ros2_ws/lidar_slam_tb3/src/dynamic_nav/dynamic_nav
ros2_ws/lidar_slam_tb3/src/dynamic_nav/launch
ros2_ws/lidar_slam_tb3/src/dynamic_nav/resource
ros2_ws/lidar_slam_tb3/src/dynamic_nav/test
ros2_ws/lidar_slam_tb3/src/my_arm_sim
ros2_ws/lidar_slam_tb3/src/my_arm_sim/my_arm_sim
ros2_ws/lidar_slam_tb3/src/my_arm_sim/resource
ros2_ws/lidar_slam_tb3/src/my_arm_sim/test
ros2_ws/lidar_slam_tb3/src/my_arm_sim/urdf
ros2_ws/lidar_slam_tb3/src/my_robot_bringup
ros2_ws/lidar_slam_tb3/src/nav_research
ros2_ws/lidar_slam_tb3/src/nav_research/config
ros2_ws/lidar_slam_tb3/src/nav_research/launch
ros2_ws/lidar_slam_tb3/src/nav_research/nav_research
ros2_ws/lidar_slam_tb3/src/nav_research/resource
ros2_ws/lidar_slam_tb3/src/nav_research/test
ros2_ws/lidar_slam_tb3/src/rl_robot
ros2_ws/lidar_slam_tb3/src/rl_robot/resource
ros2_ws/lidar_slam_tb3/src/rl_robot/rl_robot
ros2_ws/lidar_slam_tb3/src/rl_robot/test
ros2_ws/lidar_slam_tb3/src/robotic_arm_advanced
ros2_ws/lidar_slam_tb3/src/robotic_arm_advanced/resource
ros2_ws/lidar_slam_tb3/src/robotic_arm_advanced/robotic_arm_advanced
ros2_ws/lidar_slam_tb3/src/robotic_arm_advanced/test
ros2_ws/lidar_slam_tb3/src/tb3_benchmark
ros2_ws/lidar_slam_tb3/src/tb3_benchmark/resource
ros2_ws/lidar_slam_tb3/src/tb3_benchmark/tb3_benchmark
ros2_ws/lidar_slam_tb3/src/tb3_benchmark/test
ros2_ws/lidar_slam_tb3/src/tb3_fsm_controller
ros2_ws/lidar_slam_tb3/src/tb3_fsm_controller/resource
ros2_ws/lidar_slam_tb3/src/tb3_fsm_controller/tb3_fsm_controller
ros2_ws/lidar_slam_tb3/src/tb3_fsm_controller/test
ros2_ws/lidar_slam_tb3/src/tb3_nav
ros2_ws/lidar_slam_tb3/src/tb3_nav/resource
ros2_ws/lidar_slam_tb3/src/tb3_nav/tb3_nav
ros2_ws/lidar_slam_tb3/src/tb3_nav/test
ros2_ws/lidar_slam_tb3/src/tb3_sim_bringup
ros2_ws/lidar_slam_tb3/src/tb3_sim_bringup/launch
ros2_ws/lidar_slam_tb3/src/tb3_sim_bringup/resource
ros2_ws/lidar_slam_tb3/src/tb3_sim_bringup/tb3_sim_bringup
ros2_ws/lidar_slam_tb3/src/tb3_sim_bringup/test
ros2_ws/lidar_slam_tb3/src/tb3_sim_bringup/worlds
ros2_ws/lidar_slam_tb3/src/tb3_slam
ros2_ws/lidar_slam_tb3/src/tb3_slam/config
ros2_ws/lidar_slam_tb3/src/tb3_slam/launch
ros2_ws/lidar_slam_tb3/src/tb3_slam/resource
ros2_ws/lidar_slam_tb3/src/tb3_slam/tb3_slam
ros2_ws/lidar_slam_tb3/src/tb3_slam/test
ros2_ws/src
ros2_ws/src/dynnav_bringup
ros2_ws/src/dynnav_bringup/config
ros2_ws/src/dynnav_bringup/launch
ros2_ws/src/dynnav_bringup/resource
ros2_ws/src/dynnav_bringup/rviz
ros2_ws/src/dynnav_nav2
ros2_ws/src/dynnav_nav2/config
ros2_ws/src/dynnav_nav2/docs
ros2_ws/src/dynnav_nav2/dynnav_nav2
ros2_ws/src/dynnav_nav2/launch
ros2_ws/src/dynnav_nav2/resource
ros2_ws/src/dynnav_nav2_benchmark
ros2_ws/src/dynnav_nav2_benchmark/config
ros2_ws/src/dynnav_nav2_benchmark/dynnav_nav2_benchmark
ros2_ws/src/dynnav_nav2_benchmark/launch
ros2_ws/src/dynnav_nav2_benchmark/models
ros2_ws/src/dynnav_nav2_benchmark/resource
ros2_ws/src/dynnav_nav2_benchmark/test
ros2_ws/src/dynnav_nav2_cpp
ros2_ws/src/dynnav_nav2_cpp/config
ros2_ws/src/dynnav_nav2_cpp/include
ros2_ws/src/dynnav_nav2_cpp/include/dynnav_nav2_cpp
ros2_ws/src/dynnav_nav2_cpp/src
ros2_ws/src/dynnav_nav2_cpp/test
ros2_ws/src/dynnav_turtlebot3
ros2_ws/src/dynnav_turtlebot3/config
ros2_ws/src/dynnav_turtlebot3/launch
ros2_ws/src/dynnav_turtlebot3/worlds
```

### `scripts/` (2 folder paths)

```text
scripts
scripts/maintenance
```

### `src/` (8 folder paths)

```text
src
src/cybersecurity_ros2
src/cybersecurity_ros2/cybersecurity_ros2
src/cybersecurity_ros2/cybersecurity_ros2/nodes
src/cybersecurity_ros2/resource
src/dynnav
src/dynnav_dashboard
src/dynnav_dashboard/contributions
```

### `test/` (1 folder paths)

```text
test
```

### `tests/` (2 folder paths)

```text
tests
tests/security
```

### `tools/` (1 folder paths)

```text
tools
```

### `utils/` (1 folder paths)

```text
utils
```

### `vercel_app/` (3 folder paths)

```text
vercel_app
vercel_app/app
vercel_app/app/simulation
```

### `website/` (4 folder paths)

```text
website
website/app
website/components
website/public
```


## Reproduction

From any authenticated GitHub REST client, request the pinned commit tree:

```text
GET https://api.github.com/repos/panagiotagrosdouli/DynNav/git/trees/b626d6e9b5bf8b8cf1ec87906597d767224f5f37?recursive=1
```

Verify `truncated=false`, then count `type=tree`, `type=blob`, and paths without a slash. A subsequent `main` commit may have a different inventory; do not silently apply these counts to future revisions.
