from __future__ import annotations

from dynnav.experiments.causal_graph_stress_benchmark import (
    run_causal_graph_stress_benchmark,
)


def test_causal_graph_stress_grid_smoke() -> None:
    result = run_causal_graph_stress_benchmark(
        trials_per_pair_grid=(100,),
        propensities=(0.2, 0.5),
        effect_scales=(0.5, 1.0),
        repetitions=2,
        seed=41,
    )
    assert len(result["raw"]) == 1 * 2 * 2 * 2
    assert len(result["summary"]) == 1 * 2 * 2

    assert all(
        0.0 <= row["precision_mean"] <= 1.0
        and 0.0 <= row["recall_mean"] <= 1.0
        for row in result["summary"]
    )

    strong = [
        row
        for row in result["summary"]
        if row["propensity"] == 0.5 and row["effect_scale"] == 1.0
    ][0]
    weak = [
        row
        for row in result["summary"]
        if row["propensity"] == 0.2 and row["effect_scale"] == 0.5
    ][0]
    assert strong["recall_mean"] >= weak["recall_mean"]
