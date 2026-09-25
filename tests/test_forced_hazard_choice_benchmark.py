from __future__ import annotations

import pytest

from dynnav.experiments.forced_hazard_choice_benchmark import (
    ForcedHazardSpec,
    forced_hazard_world,
    frozen_forced_hazard_specs,
    run_forced_hazard_choice_benchmark,
    summarize_forced_hazard_choice,
)
from dynnav.experiments.commitment_execution_benchmark import _activated_indices
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.experiments.commitment_execution_benchmark import _state_only_marginal_hazard


def test_frozen_specs_are_deterministic() -> None:
    left = frozen_forced_hazard_specs(count=8, seed=260925)
    right = frozen_forced_hazard_specs(count=8, seed=260925)
    assert left == right
    assert len(left) == 8


def test_every_planned_route_must_activate_one_of_two_terminal_hazards() -> None:
    spec = ForcedHazardSpec(0, 1, 0.8, 0.2)
    grid, start, goal, safe, model = forced_hazard_world(spec)

    shortest = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells=safe,
        hazard_model=model,
        mode=CommitmentPlannerMode.SHORTEST,
    )
    history = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells=safe,
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(recoverability_weight=8.0),
    )

    assert len(_activated_indices(model, tuple(shortest.path))) == 1
    assert len(_activated_indices(model, tuple(history.path))) == 1


def test_exact_state_only_control_and_history_use_same_oracle_but_choose_differently() -> None:
    spec = ForcedHazardSpec(0, 1, 0.8, 0.2)
    grid, start, goal, safe, model = forced_hazard_world(spec)

    state_only = hazard_reliability_astar(
        grid,
        start,
        goal,
        safe_cells=safe,
        hazard=_state_only_marginal_hazard(model),
        mode=HazardReliabilityMode.EXACT_RETURN,
        config=HazardReliabilityAStarConfig(
            reliability_weight=8.0,
            max_hazard_cells=16,
        ),
    )
    history = commitment_aware_astar(
        grid,
        start,
        goal,
        safe_cells=safe,
        hazard_model=model,
        mode=CommitmentPlannerMode.HISTORY_AWARE,
        config=CommitmentAwareAStarConfig(
            recoverability_weight=8.0,
            max_hazard_cells=16,
        ),
    )

    state_active = _activated_indices(model, tuple(state_only.path))
    history_active = _activated_indices(model, tuple(history.path))
    assert state_active == {0}
    assert history_active == {1}
    assert state_only.geometric_length == 7
    assert history.geometric_length == 9


def test_history_route_matches_prederived_terminal_trigger_boundary() -> None:
    specs = (
        ForcedHazardSpec(0, 1, 0.8, 0.2),
        ForcedHazardSpec(1, 2, 0.9, 0.2),
        ForcedHazardSpec(2, 3, 0.95, 0.10),
        ForcedHazardSpec(3, 2, 0.40, 0.35),
    )
    records = run_forced_hazard_choice_benchmark(
        specs=specs,
        trial_seeds=(0, 1, 2),
        recoverability_weight=8.0,
    )
    summary = summarize_forced_hazard_choice(records)
    assert summary["history_analytic_route_match_rate"] == pytest.approx(1.0)
    assert summary["history_differs_from_state_only_scenarios"] >= 2


def test_unavoidable_suite_never_reports_zero_activated_hazards() -> None:
    records = run_forced_hazard_choice_benchmark(
        specs=frozen_forced_hazard_specs(count=6),
        trial_seeds=(0, 1, 2),
        recoverability_weight=8.0,
    )
    assert records
    assert all(row.activated_hazard in (0, 1) for row in records)
    assert all(row.activated_probability > 0.0 for row in records)
