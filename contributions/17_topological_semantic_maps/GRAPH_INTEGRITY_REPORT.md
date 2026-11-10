# C17 — Semantic graph persistence, deterministic grounding and route repair

## Executed implementation changes

The original C17 prototype previously relied on Python's process-randomized `hash(label)` to create label-stub embeddings. Consequently, different processes and Python hash seeds assigned **different embeddings to identical semantic labels**. That undermines cross-process ROS2 semantic query transfer and reproducibility. The module now derives a stable seed from the SHA-256 of the label before creating its explicitly synthetic/random embedding.

The original `TopologicalSemanticMap.to_dict()` omitted the node embeddings, so serialized and restored graph nodes lost their semantic grounding functionality. The new format serializes embedding vectors. Its loader validates finite embeddings, preserves the actual recorded node IDs (including non-contiguous IDs), reconstructs the original directed/passable edge set and resets the next available node ID safely.

Additional fail-closed checks reject nonexistent edge endpoints, negative or non-finite edge weights, non-finite and dimension-mismatched embeddings, invalid centroids and untrusted serialized edges.

## Actual executable tests and benchmark

Dedicated workflow: [C17 semantic integrity](https://github.com/panagiotagrosdouli/DynNav/actions/workflows/c17-semantic-integrity.yml). The workflow executes:

1. Cross-process semantic stub embeddings with different `PYTHONHASHSEED` values.
2. Exact semantic grounding and blocked-edge preservation through JSON serialization/reload.
3. Non-contiguous semantic node IDs and graph route planning.
4. Fail-closed malformed graph and embedding inputs.
5. The original canonical C17 six-label semantic grounding and two-route blocked-transition planning benchmark, with CSV and GitHub Actions evidence artifact.

**Important research classification:** These are *actual software integration tests on synthetic semantic maps*, not a real CLIP/VLM model, actual scene segmentation, independently grounded real robot observations, a real-world metric-topological map or physical robot experiments.

## Replication

```bash
python -m pip install numpy pytest
python -m pytest -q contributions/17_topological_semantic_maps/tests
python contributions/17_topological_semantic_maps/experiments/eval_topo_semantic_navigation.py --out /tmp/c17_benchmark.csv
```

## Missing scientific and physical evidence

The semantic label matching is still a deterministic random **stub**, even after the cross-process fix. Matching a label to a synthetic embedding of the exact same string is a trivial identity fixture, **not open-vocabulary semantic recognition accuracy**. There is no physical Dingo controlled by C17, no camera-to-label benchmark, no validated loop closure or robot execution.

Future actual-data validation requires real sensor observations, independently annotated semantic regions, a trained/frozen embedding model if that is the stated claim, split by environment/session, a topological-to-metric anchoring evaluation, blocked passage replay and supervised physical navigation.

**Physical C17 navigation trials verified: 0.**
