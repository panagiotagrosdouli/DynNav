from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.history_compression import (
    build_hazard_event_quotient,
    quotient_return_probability,
)
from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import (
    TopologyHazardBelief,
    exact_safe_return_probability,
)


def test_event_quotient_preserves_return_probability_for_duplicate_triggers() -> None:
    grid = GridMap.from_obstacles(3, 1)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((0, 0), (1, 0)),
                closure_cell=(1, 0),
                closure_probability=0.5,
            ),
            CommitmentClosure(
                trigger=((2, 0), (1, 0)),
                closure_cell=(1, 0),
                closure_probability=0.5,
            ),
        )
    )
    model.validate(grid)
    quotient = build_hazard_event_quotient(model)

    active_from_first = quotient.compress_active_indices(frozenset({0}))
    active_from_second = quotient.compress_active_indices(frozenset({1}))
    assert active_from_first == active_from_second == frozenset({0})

    expected = exact_safe_return_probability(
        grid,
        (2, 0),
        {(0, 0)},
        TopologyHazardBelief({(1, 0): 0.5}),
    )
    first = quotient_return_probability(
        grid,
        (2, 0),
        {(0, 0)},
        quotient,
        active_from_first,
    )
    second = quotient_return_probability(
        grid,
        (2, 0),
        {(0, 0)},
        quotient,
        active_from_second,
    )

    assert expected == pytest.approx(0.5)
    assert first == pytest.approx(expected)
    assert second == pytest.approx(expected)
