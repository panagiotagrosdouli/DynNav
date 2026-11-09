# Real-Data Evidence Matrix

| Contribution area | Real-data evidence present | Supports | Does not support |
|---|---|---|---|
| C00 / localization and map ingestion | PR #210 documents LILocBench `dynamics_0`: 3,194 poses, 159.951 s, 53.967 m path, mean XY speed 0.337 m/s; plot in `website/public/`. | Descriptive statistics for a real Clearpath Dingo recording. | No DynNav comparison, map replay, causal effect, action-triggered closure, or planner efficacy. Raw pose input absent locally in this audit; not independently recomputed. |
| C01 | `.pt` checkpoint files exist in tree. | File presence only. | Training provenance and evaluation unverified; `torch` absent. |
| C02-C26 | Canonical suite is synthetic/controlled per registry. | Software behavior on declared fixtures. | Real-data validity, sensor calibration, or generalization. |
| C27 | None. | Conceptual research agenda. | Independent empirical or theoretical validation. |

The only real-world evidence identified in reviewed files is descriptive LILocBench analysis from merged PR #210. It does not show that DynNav improved navigation. LILocBench license is CC BY-NC-SA 4.0; follow attribution and non-commercial/share-alike requirements.
