# Evaluation Protocol

DynNav experiments are expected to be reproducible from a clean checkout.

## Required reporting

Every benchmark should report:

- YAML configuration path;
- deterministic seed range;
- scenario count;
- success rate;
- path length distribution;
- terminal risk distribution;
- recoverability distribution;
- planning node expansions;
- generated CSV path;
- code commit hash.

## Baselines

The minimum baseline is an equivalent geometric planner with risk and returnability weights set to zero. More advanced baselines may include D*, D* Lite, Nav2 Smac Planner, and sampling-based planners under the same scenarios.

## Statistical treatment

Single-seed results are not sufficient for validation. Report means and variance across multiple deterministic seeds. Mark components as **Validated** only when benchmark scripts, seed ranges, and CI smoke tests all support the claim.

## Failure handling

Failed planning episodes must remain in the CSV output. Omitting failures biases reported performance.
