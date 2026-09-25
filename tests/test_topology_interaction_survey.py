from __future__ import annotations

from dynnav.experiments.topology_interaction_survey import (
    run_topology_interaction_survey,
)


def test_held_out_topology_survey_contains_both_dependence_signs() -> None:
    rows = run_topology_interaction_survey(
        accepted_maps=20,
        obstacle_probability=0.30,
        seed=20260925,
    )
    assert len(rows) == 20
    assert all(
        row.hazard_pairs
        == row.negative_interactions + row.zero_interactions + row.positive_interactions
        for row in rows
    )
    assert sum(row.negative_interactions for row in rows) > 0
    assert sum(row.positive_interactions for row in rows) > 0
