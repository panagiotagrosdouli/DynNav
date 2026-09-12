from __future__ import annotations

import json

from dynnav.experiments.hazard_planner_pilot import (
    run_hazard_planner_pilot,
    summarize_hazard_planner_pilot,
    write_hazard_planner_pilot_artifacts,
)
from dynnav.planners.hazard_reliability_astar import HazardReliabilityMode


def test_planner_pilot_emits_every_mode_for_every_seed() -> None:
    records = run_hazard_planner_pilot((0, 1, 2), hazard_count=4)

    assert len(records) == 3 * len(HazardReliabilityMode)
    assert {row.mode for row in records} == {mode.value for mode in HazardReliabilityMode}


def test_planner_pilot_is_deterministic_except_runtime_measurement() -> None:
    first = run_hazard_planner_pilot((0, 1), hazard_count=4)
    second = run_hazard_planner_pilot((0, 1), hazard_count=4)

    for left, right in zip(first, second, strict=True):
        assert left.seed == right.seed
        assert left.mode == right.mode
        assert left.success == right.success
        assert left.geometric_length == right.geometric_length
        assert left.nodes_expanded == right.nodes_expanded
        assert left.minimum_exact_return_probability == right.minimum_exact_return_probability
        assert left.mean_exact_return_probability == right.mean_exact_return_probability
        assert left.estimated_minimum_return_probability == right.estimated_minimum_return_probability
        assert left.cumulative_return_fragility == right.cumulative_return_fragility


def test_planner_pilot_summary_is_auditable() -> None:
    records = run_hazard_planner_pilot((0, 1, 2), hazard_count=4)
    summary = summarize_hazard_planner_pilot(records)

    for mode in HazardReliabilityMode:
        row = summary[mode.value]
        assert row["trials"] == 3
        assert 0.0 <= row["success_rate"] <= 1.0
        assert 0.0 <= row["mean_minimum_exact_return_probability"] <= 1.0


def test_planner_pilot_writes_raw_artifacts(tmp_path) -> None:
    records = run_hazard_planner_pilot((0, 1), hazard_count=4)
    write_hazard_planner_pilot_artifacts(records, tmp_path)

    assert (tmp_path / "trials.csv").exists()
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload[HazardReliabilityMode.SHORTEST.value]["trials"] == 2
