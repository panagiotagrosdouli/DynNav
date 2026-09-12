from __future__ import annotations

import json

import pytest

from dynnav.experiments.history_commitment_benchmark import (
    run_history_commitment_benchmark,
    write_history_commitment_artifacts,
)


def test_shortest_return_probability_tracks_trigger_closure_probability() -> None:
    records = run_history_commitment_benchmark(
        closure_probabilities=(0.2, 0.8),
        recoverability_weights=(4.0,),
    )
    shortest = [row for row in records if row.mode == "shortest"]

    assert [row.geometric_length for row in shortest] == [3, 3]
    assert [row.activated_closure_count for row in shortest] == [1, 1]
    assert [row.final_return_probability for row in shortest] == pytest.approx([0.8, 0.2])


def test_history_aware_planner_switches_from_direct_to_detour_as_hazard_rises() -> None:
    records = run_history_commitment_benchmark(
        closure_probabilities=(0.2, 0.8),
        recoverability_weights=(4.0,),
    )
    history = [row for row in records if row.mode == "history_aware"]

    low, high = history
    assert low.geometric_length == 3
    assert low.activated_closure_count == 1
    assert low.final_return_probability == pytest.approx(0.8)

    assert high.geometric_length == 5
    assert high.activated_closure_count == 0
    assert high.final_return_probability == pytest.approx(1.0)


def test_zero_or_weak_recoverability_pressure_does_not_force_detour() -> None:
    records = run_history_commitment_benchmark(
        closure_probabilities=(0.8,),
        recoverability_weights=(0.5,),
    )
    history = next(row for row in records if row.mode == "history_aware")

    assert history.geometric_length == 3
    assert history.activated_closure_count == 1


def test_history_benchmark_writes_traceable_artifacts(tmp_path) -> None:
    records = run_history_commitment_benchmark(
        closure_probabilities=(0.2, 0.8),
        recoverability_weights=(1.0, 4.0),
    )
    write_history_commitment_artifacts(records, tmp_path)

    assert (tmp_path / "trials.csv").exists()
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload["probability_levels"] == 2
    assert payload["weight_levels"] == 2
