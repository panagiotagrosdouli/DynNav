from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.history_compression import build_hazard_event_quotient
from dynnav.history_compression_objective import quotient_path_objective_witness
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    commitment_aware_astar,
)
from dynnav.planners.compressed_commitment_astar import (
    CompressedCommitmentAStarConfig,
    compressed_commitment_astar,
)
from dynnav.planners.grid_map import GridMap


def _duplicate_event_problem() -> tuple[GridMap, CommitmentHazardModel]:
    grid = GridMap.from_obstacles(5, 3)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((1, 1), (2, 1)),
                closure_cell=(1, 0),
                closure_probability=0.6,
            ),
            CommitmentClosure(
                trigger=((1, 2), (2, 2)),
                closure_cell=(1, 0),
                closure_probability=0.6,
            ),
            CommitmentClosure(
                trigger=((2, 1), (3, 1)),
                closure_cell=(2, 0),
                closure_probability=0.3,
            ),
        )
    )
    return grid, model


def test_quotient_preserves_return_profile_and_objective_for_concrete_path() -> None:
    grid, model = _duplicate_event_problem()
    path = ((0, 1), (1, 1), (2, 1), (3, 1), (4, 1))

    witness = quotient_path_objective_witness(
        grid,
        path,
        safe_cells={(0, 1)},
        hazard_model=model,
        step_cost=1.0,
        recoverability_weight=7.0,
    )

    assert witness.return_profile_preserved
    assert witness.objective_preserved
    assert witness.raw_total_cost == pytest.approx(witness.quotient_total_cost)
    assert witness.steps[-1].raw_active == frozenset({0, 2})
    assert witness.steps[-1].quotient_active == frozenset({0, 1})


def test_duplicate_trigger_identity_does_not_change_path_objective() -> None:
    grid, model = _duplicate_event_problem()
    path = ((2, 2), (3, 2), (4, 2))

    first = quotient_path_objective_witness(
        grid,
        path,
        safe_cells={(0, 1)},
        hazard_model=model,
        initial_activated_closures=frozenset({0}),
        recoverability_weight=5.0,
    )
    second = quotient_path_objective_witness(
        grid,
        path,
        safe_cells={(0, 1)},
        hazard_model=model,
        initial_activated_closures=frozenset({1}),
        recoverability_weight=5.0,
    )

    assert first.objective_preserved and second.objective_preserved
    assert first.raw_total_cost == pytest.approx(second.raw_total_cost)
    assert first.quotient_total_cost == pytest.approx(second.quotient_total_cost)
    assert [s.raw_return_probability for s in first.steps] == pytest.approx(
        [s.raw_return_probability for s in second.steps]
    )


def test_compressed_and_raw_astar_have_same_optimal_objective() -> None:
    grid, model = _duplicate_event_problem()
    raw = commitment_aware_astar(
        grid,
        (0, 1),
        (4, 1),
        safe_cells={(0, 1)},
        hazard_model=model,
        config=CommitmentAwareAStarConfig(
            step_cost=1.0,
            recoverability_weight=3.0,
            heuristic_weight=1.0,
        ),
    )
    compressed = compressed_commitment_astar(
        grid,
        (0, 1),
        (4, 1),
        safe_cells={(0, 1)},
        hazard_model=model,
        config=CompressedCommitmentAStarConfig(
            step_cost=1.0,
            recoverability_weight=3.0,
            heuristic_weight=1.0,
        ),
    )

    assert raw.success and compressed.success
    assert compressed.cost == pytest.approx(raw.cost)
    assert compressed.final_return_probability == pytest.approx(
        raw.final_return_probability
    )
    assert compressed.minimum_return_probability == pytest.approx(
        raw.minimum_return_probability
    )


def test_quotient_never_merges_distinct_future_event_semantics() -> None:
    grid = GridMap.from_obstacles(4, 2)
    model = CommitmentHazardModel(
        (
            CommitmentClosure(((0, 0), (1, 0)), (2, 0), 0.5),
            CommitmentClosure(((0, 1), (1, 1)), (2, 1), 0.5),
            CommitmentClosure(((1, 0), (2, 0)), (2, 0), 0.7),
        )
    )
    model.validate(grid)
    quotient = build_hazard_event_quotient(model)
    assert quotient.event_count == 3
