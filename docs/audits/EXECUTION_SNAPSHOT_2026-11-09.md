# DynNav execution snapshot — 2026-11-09

This snapshot records what was checked during the repository audit and what the resulting evidence supports. It is not a claim that every research track is validated or that a physical robot trial has been completed.

## Repository and CI state

- The `real-data-validation` pull request #210 was merged into `main` as `b626d6e9b5bf8b8cf1ec87906597d767224f5f37` on 2026-11-09.
- Research portal changes are proposed in draft pull request #211, commit `4b1761137b050015fce76252364b6ed76e2b7cc5`. The proposal adds generated C01–C26 contribution pages and improves evidence links and scientific-boundary statements.
- Pull request #211 CI completed successfully: Python 3.10, 3.11, and 3.12; ROS 2 Jazzy/Nav2 plugin; researcher and website builds; documentation inventory and local-link checks. The web-portal job also verified the generated contribution catalog, dependency trees, both portal builds, and both portal entry points.
- On the same base tree before the portal-only changes, the full Python suite completed with 682 passed, 32 skipped, and one Starlette/httpx deprecation warning; total reported coverage was 85%.
- The contribution smoke workflow completed at workflow level on the same base tree. Its retained artifact reports 25 tracks passed and C01 skipped because optional PyTorch was unavailable. These are controlled synthetic implementation checks, not independent real-world validation.

## Evidence observed

### Contribution smoke experiments

The C01–C26 workflow artifact contains examples that should remain visible alongside positive outcomes:

- C03 selects a longer route at the largest tested risk weight, with lower synthetic CVaR and an approximately 11.4% longer route in that case. This is a controlled trade-off example, not evidence of general superiority.
- C21 reports zero success for both PPO and shielded PPO in the retained smoke setup, compared with 0.625 for the greedy baseline. The artifact does not support a trained-policy advantage claim.
- C22's adaptive, fixed, and reverse curriculum settings produce identical outcomes and do not progress beyond the easiest stage. The artifact does not demonstrate a curriculum benefit.

These results should be interpreted with their registered scenarios, seeds, and metrics. Smoke-test passage establishes that an experiment path executes and emits its contract; it does not establish external validity.

### Manuscript and protocol

- `paper/dynnav_r/evidence_manifest.json` parses as valid JSON, and `paper/dynnav_r/check_submission.py` passes. The manifest has 22 unique citations; the checker confirms the recorded V3 abstract claims and the protocol's 96 scenarios / 250 paired seeds.
- The submission checker is a consistency check. It does not independently establish novelty, dataset validity, or acceptance readiness.
- The latest successful paper workflow available during this audit was run `41301966322` on 2026-11-01 at commit `e5246c…`; it reported provenance, citation, LaTeX, page-count, and unresolved-reference checks as successful.
- Local LaTeX compilation could not be reproduced because the host's TeX installation lacks `pdflatex.fmt`.

### Public trajectory data

`docs/LILOCBENCH_DYNAMICS_0_ANALYSIS.md` records descriptive analysis of 3,194 ground-truth poses spanning 159.951 s and 53.967 m, with mean speed 0.337 m/s and observed sampling gaps. The repository does not retain the raw LILocBench map, pose sequence, or bag needed to independently rerun the analysis in this environment. `docs/REAL_DATA_VALIDATION.md` correctly distinguishes trajectory analysis from map-backed replay and matched planner comparison. No causal planner-efficacy claim is supported by this trajectory summary. The dataset's stated license is CC BY-NC-SA 4.0.

### ROS 2, Nav2, Gazebo, and hardware

- The ROS 2 Jazzy/Nav2 plugin CI job passed during pull request #211.
- The latest successful Gazebo benchmark workflows available during this audit were `41301972122` and `41301964907`, both on 2026-11-01 at `e5246c…`. They cover paired planner-server and action-triggered simulation protocols with retained artifacts. They predate the 2026-11-09 merge, and they are simulation evidence, not physical-robot evidence.
- ROS 2, Gazebo, and Docker executables are not available in the local host, so those simulations could not be rerun locally.
- No physical-robot run or associated raw hardware log was verified in this audit.

## Portal and deployment state

- The canonical contribution catalog is generated from `configs/contributions/registry.yaml`, `configs/contributions/experiments.yaml`, and `src/dynnav_dashboard/contribution_registry.yaml`; the script's `--check` mode verified all 26 ordered entries and linked repository paths.
- The existing published GitHub Pages research guide was reachable during review and contains the detailed model, retained results, negative findings, ROS 2 architecture, and limitations. The proposed portal links to that guide.
- Pull request #211's portal build passed, but the GitHub Pages deployment step was skipped by the workflow's manual deployment gate. No deployment was triggered.
- No DynNav Vercel project or deployment was linked to the connected Vercel account during inspection. Therefore no Vercel deployment was created or verified.
- Local Next.js production build attempts failed on the host with `ENOENT: no such file or directory, uv_resident_set_memory`. The equivalent GitHub Actions web-portal build passed on the pull request.

## Remaining evidence required for stronger claims

1. Preserve or attach the licensed LILocBench map, pose sequence, and bag, with checksums and provenance, so the descriptive analysis can be independently reproduced.
2. Run matched planner comparisons on the public map/sequence with the frozen protocol, pre-registered metrics, paired seeds where applicable, and retained raw outputs.
3. Run and archive a physical-robot trial before making hardware-efficacy claims.
4. Use the authorized deployment path and verify the deployed URL after pull request #211 is reviewed and merged. This snapshot does not authorize or record deployment.

## Reproduction pointers

- Contribution protocol: [`EXPERIMENT_PROTOCOL_V3.md`](../../EXPERIMENT_PROTOCOL_V3.md)
- Contribution registry: [`configs/contributions/experiments.yaml`](../../configs/contributions/experiments.yaml)
- Claim-evidence matrix: [`CLAIM_EVIDENCE_MATRIX.md`](../../CLAIM_EVIDENCE_MATRIX.md)
- Real-data validation scope: [`docs/REAL_DATA_VALIDATION.md`](../REAL_DATA_VALIDATION.md)
- Gazebo protocol: [`docs/GAZEBO_BENCHMARK_PROTOCOL.md`](../GAZEBO_BENCHMARK_PROTOCOL.md)
- Manuscript evidence manifest: [`paper/dynnav_r/evidence_manifest.json`](../../paper/dynnav_r/evidence_manifest.json)
