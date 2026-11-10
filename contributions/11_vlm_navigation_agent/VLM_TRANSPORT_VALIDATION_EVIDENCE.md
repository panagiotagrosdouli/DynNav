# C11 — Verified VLM transport integration and goal-validation gate

**Date:** 2026-11-10  
**Evidence level:** Executed software/HTTP protocol and deterministic semantic-safety validation; **NOT a live trained vision-language model or physical robot experiment**.

## Verified execution

[GitHub Actions #42788341830](https://github.com/panagiotagrosdouli/DynNav/actions/runs/42788341830) **passed: 21 tests** and six goal-validation fixture scenarios. The regression tests exercised actual network loopback HTTP serialization using a deterministic local server compatible with both Ollama `/api/chat` and OpenAI-style `/chat/completions`; the received image bytes were checked to begin with the actual JPEG marker. No cloud or real local VLM inference was performed.

In the six goal-validation fixtures, one valid corridor goal was `ACCEPT`; the remaining five low-confidence, hallucinated-region, out-of-frame pixel, distant waypoint and forbidden-semantics cases were **not accepted** (rejected or human-review). These are six designed fixtures, not a statistically valid safety failure-rate estimate.

## Repairs tested

- Live VLM responses now pass through the repository's existing goal validator before a semantic target is returned or counted as accepted.
- JSON decoding requires a proper dictionary, nonempty semantic goal and region, finite confidence in [0,1], and two exact-integer pixel coordinates if either is supplied. Fenced JSON is parsed without the historical character-stripping `lstrip` bug.
- Out-of-frame pixel coordinates and wrong RGB/depth array formats fail closed. Invalid, negative or missing depth no longer returns the current robot location as a fictitious valid destination.
- When configured with `require_metric_waypoint=True`, semantic-only goals do not automatically become navigation targets without valid depth-derived metric projection.
- Ollama and OpenAI-compatible requests use distinct correct multimodal image schemas; JPEG encoding requires Pillow rather than incorrectly representing NumPy raw bytes as a JPEG frame. Hosted OpenAI use requires an explicitly provided `C11_VLM_API_KEY` environment variable.
- The validation gate continues to be rule-based. Passing the gate is not a semantic-grounding or collision-free guarantee.

## Reproduction

```bash
python -m pytest -q contributions/11_vlm_navigation_agent/tests
python contributions/11_vlm_navigation_agent/experiments/eval_vlm_goal_validation.py \
  --out results/c11_integrity/validation_fixture.csv
```

[Workflow](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c11-vlm-integrity.yml) retains the six-scenario CSV and executes real local HTTP transport tests in CI.

## Explicit scientific/hardware gaps

- Actual VLM inference on labeled real RGB scenes: **not performed by this CI**.
- VLM goal accuracy/precision on independent physical-world frames: **not established**.
- Calibrated camera intrinsics, geometrically verified 3D semantic grounding: **not established**.
- Actual ROS 2/Nav2 navigation controlled by C11 decisions: **not demonstrated**.
- Physical robot navigation controlled by C11: **zero verified trials**.

The past static rule-based C11 eight-scene benchmark must not be relabeled as VLM model inference. A source image or archived robot recording alone does not establish that a VLM made those navigation decisions. Stronger validation requires a known running model with a recorded exact checkpoint/model ID, independent labeled real RGB-D data, repeated trials, masked or unsafe-goal stress tests, safe ROS 2 mission gating, and actual physical supervised navigation if hardware claims are made.
