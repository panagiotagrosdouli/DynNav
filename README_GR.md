# DynNav

**Συγγραφέας / Researcher:** Panagiota Grosdouli

**History-conditioned safe-return planning για αυτόνομα ρομπότ με action-triggered topology hazards.**

Το DynNav μελετά ένα συγκεκριμένο failure mode στη δυναμική πλοήγηση: δύο εκτελέσεις μπορούν να φτάσουν στο **ίδιο γεωμετρικό state**, αλλά να έχουν διαφορετική μελλοντική recoverability επειδή προηγούμενες ενέργειες του ρομπότ ενεργοποίησαν διαφορετικά environmental hazards.

[English](README.md) · [Ελληνικά](README_GR.md) · [Repository guide](docs/REPOSITORY_GUIDE.md) · [IEEE paper](paper/dynnav_r/main.tex)

> **Κατάσταση:** ενεργό research prototype με retained synthetic/geometric evidence, C++ Nav2 planner και frozen action-triggered Gazebo protocol. Δεν γίνεται claim για safety certification, universal superiority ή physical-robot efficacy.

## Ερευνητικό ερώτημα

> **Μεταφέρει το path history πληροφορία σχετική με τη recoverability που χάνεται σε state-only future-risk models όταν οι ενέργειες του ρομπότ ενεργοποιούν μελλοντικά topology hazards;**

Ο publication-facing planner δουλεύει σε augmented state:

```text
(grid cell, activated hazard history)
```

Το persistent history ενημερώνεται μόνο από **executed transitions**, όχι από planned/imagined transitions.

## Τι έχει υλοποιηθεί

| Layer | Υλοποίηση |
|---|---|
| Planning | shortest, risk-aware, exact history-aware, critical-cut και hard safe-return planners |
| Hazard model | directed action-triggered stochastic topology closures |
| Recoverability | exact future-closure oracle και online approximations |
| Evaluation | paired CRN trials, bootstrap intervals, McNemar/TOST utilities |
| ROS 2 / Nav2 | C++17 `nav2_core::GlobalPlanner` με persistent executed-history state |
| Gazebo | static, time-triggered dynamic και frozen action-triggered protocols |
| Paper | IEEE manuscript με machine-readable evidence manifest και provenance checks |
| Interfaces | Streamlit lab και FastAPI / Next.js research workspace |

Το παλιότερο J0–J3 risk/recoverability layer παραμένει ως controlled research history. Το σημερινό paper core είναι το στενότερο **history-conditioned safe-return** problem.

## Retained evidence snapshot

| Study | State-only / shortest | History-conditioned | Scope |
|---|---:|---:|---|
| 3-module execution, `p=0.8` | 0.992 failure | 0 failure | controlled mechanism |
| Held-out 6/7/8 modules | 0.992 / 0.998 / 1.000 | 0 / 0 / 0 | probability/horizon generalization |
| Fork / L-room / chamber | 0.810 / 0.756 / 0.890 | 0 / 0 / 0 | τρεις frozen hand-authored topologies |
| Joint-cut counterexample | — | cut approximation διαφωνεί με exact σε 9/9 settings | explicit failure boundary |

Το geometric Pareto experiment έδειξε επίσης ότι hard safe-return constraints μπορούν να βρουν το ίδιο safe route σε αυτά τα worlds. Άρα το supported result αφορά κυρίως το **history representation** και όχι claim ότι ένα soft objective κερδίζει πάντα τα hard constraints.

Η authoritative provenance είναι στα [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) και [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md).

## Paper

**When the Same Place Is Not the Same State: History-Conditioned Safe-Return Planning under Action-Triggered Topology Hazards**

Το contribution είναι σκόπιμα στενό: action-triggered degradation του return-connectivity, same-state/different-history aliasing, exact augmented-state planning, critical-cut approximation με καταγεγραμμένο adversarial boundary, held-out evaluation και ROS 2/Nav2 integration.

Δεν παρουσιάζονται ως novel τα generic recoverability, safe-return constraints, history-dependent costs ή decision-dependent uncertainty.

## Reviewer path

1. [`paper/dynnav_r/main.tex`](paper/dynnav_r/main.tex) — το επιστημονικό argument και τα αποτελέσματα.
2. [`paper/dynnav_r/evidence_manifest.json`](paper/dynnav_r/evidence_manifest.json) — provenance των runs/artifacts.
3. [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md) — canonical code/evidence map.
4. [`CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) — τι υποστηρίζεται και τι όχι.
5. [`dynnav/commitment_hazard.py`](dynnav/commitment_hazard.py) — history-trigger model.
6. [`dynnav/planners/commitment_aware_astar.py`](dynnav/planners/commitment_aware_astar.py) — exact reference planner.
7. [`ros2_ws/src/dynnav_nav2_cpp`](ros2_ws/src/dynnav_nav2_cpp) — C++ Nav2 planner.
8. [`ros2_ws/src/dynnav_nav2_benchmark`](ros2_ws/src/dynnav_nav2_benchmark) — ROS/Gazebo validation.

## Canonical repository map

```text
dynnav/                         Python research core
ros2_ws/src/dynnav_nav2_cpp/    C++ Nav2 planner
ros2_ws/src/dynnav_nav2_benchmark/ ROS/Gazebo benchmark
paper/dynnav_r/                  IEEE paper + evidence manifest
results/                         retained experiment outputs
scripts/                         reproducible runners και audits
tests/                           regression/research-contract tests
configs/                         experiment configuration
docs/                            scientific + engineering documentation
app/                             Streamlit research lab
apps/api/ + apps/web/            research API/workspace
contributions/                   exploratory programme, όχι paper evidence
```

Παλαιότερα top-level modules παραμένουν για compatibility και historical experiments. Δεν θεωρούνται όλα validated contributions. Η διάκριση υπάρχει στο [`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md).

## Reproduce το Python core

```bash
git clone https://github.com/panagiotagrosdouli/DynNav.git
cd DynNav
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,researcher,dashboard]"
ruff check dynnav ros2_ws/src/dynnav_nav2_benchmark
python -m pytest -q
```

## ROS 2 Jazzy / Nav2

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths ros2_ws/src --ignore-src --rosdistro jazzy -r -y
colcon build --base-paths ros2_ws/src --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
source install/setup.bash
colcon test --packages-select dynnav_nav2_cpp dynnav_nav2_benchmark
```

Το πρώτο action-triggered Gazebo scenario παγώθηκε πριν από comparative outcomes: trigger `(174,189) -> (175,189)`, closure cell `(181,191)`, probability `0.8`. Νέα Gazebo efficacy claims μπαίνουν μόνο αν υπάρχουν valid retained execution artifacts.

## Evidence discipline

Publication-facing claim σημαίνει implementation, deterministic regression coverage, frozen config/seed policy, retained machine-readable output, provenance, σωστή paired/statistical analysis και explicit limitation/failure boundary.

Η ισχυρότερη evidence βάση παραμένει simulation/grid based. Το επόμενο hardening βήμα είναι paired retained action-triggered Gazebo execution και μετά partial-observability / probability-miscalibration stress tests, εφόσον το execution evidence είναι valid.

[Repository guide](docs/REPOSITORY_GUIDE.md) · [Claims](CLAIM_EVIDENCE_MATRIX.md) · [Protocol](EXPERIMENT_PROTOCOL_V2.md) · [Failure cases](FAILURE_CASES.md) · [Contributing](CONTRIBUTING.md) · [Citation](CITATION.cff) · [License](LICENSE)
