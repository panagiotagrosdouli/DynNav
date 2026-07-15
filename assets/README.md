# Assets

This directory stores diagrams, figures, GIFs, and other media referenced by the repository documentation.

**Status:** Generated explanatory media is **Implemented** where a producing script exists. Media is not experimental evidence unless it is generated from traceable result files.

## Conventions

- `readme/`: landing-page diagrams such as `dynnav_living_map.svg`.
- `figures/`: generated or manuscript-facing figures when present.
- `demo.gif`: preferred lightweight demonstration artifact when present.

## Generation

From the repository root:

```bash
python scripts/generate_research_assets.py
python scripts/make_demo_gif.py
```

## Evidence policy

- Diagrams must be labelled conceptual when they are not generated from experiment data.
- GIFs and videos must identify whether they are synthetic, simulation-only, or hardware-derived.
- Do not manually edit quantitative labels that can be generated from raw results.
- Missing optional codecs must be reported as skipped or failed output, not as successful MP4 generation.

Related material: [`../results/README.md`](../results/README.md), [`../scripts/README.md`](../scripts/README.md), and the [root README](../README.md).
