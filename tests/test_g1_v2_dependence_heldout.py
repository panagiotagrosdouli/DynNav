from __future__ import annotations

import pytest

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.g1_v2_dependence_heldout import (
    frozen_g1_v2_scenarios,
    run_g1_v2_heldout_benchmark,
)
from dynnav.planners.scenario_commitment_astar import (
    JointDependenceMode,
    scenario_belief_for_active,
)


def _two_hazard_model() -> CommitmentHazardModel:
    return CommitmentHazardModel(
        (
            CommitmentClosure(((0, 0), (1, 0)), (2, 0), 0.5),
            CommitmentClosure(((0, 1), (1, 1)), (2, 1), 0.5),
        )
    )


def _as_distribution(model, dependence):
    belief = scenario_belief_for_active(
        model,
        frozenset({0, 1}),
        dependence,
        common_cause_mixture_weight=0.5,
    )
    return {
        scenario.closed_cells: scenario.probability
        for scenario in belief.scenarios
    }


def test_true_joint_reference_distributions_preserve_half_marginals() -> None:
    model = _two_hazard_model()
    first = model.closures[0].closure_cell
    second = model.closures[1].closure_cell

    independent = _as_distribution(
        model,
        JointDependenceMode.INDEPENDENT,
    )
    assert independent[frozenset()] == pytest.approx(0.25)
    assert independent[frozenset({first})] == pytest.approx(0.25)
    assert independent[frozenset({second})] == pytest.approx(0.25)
    assert independent[frozenset({first, second})] == pytest.approx(0.25)

    common = _as_distribution(
        model,
        JointDependenceMode.COMMON_CAUSE,
    )
    assert common == {
        frozenset(): pytest.approx(0.5),
        frozenset({first, second}): pytest.approx(0.5),
    }

    anti = _as_distribution(
        model,
        JointDependenceMode.ANTI_CORRELATED,
    )
    assert anti == {
        frozenset({first}): pytest.approx(0.5),
        frozenset({second}): pytest.approx(0.5),
    }

    mixture = _as_distribution(
        model,
        JointDependenceMode.PARTIAL_MIXTURE,
    )
    assert mixture[frozenset()] == pytest.approx(0.375)
    assert mixture[frozenset({first})] == pytest.approx(0.125)
    assert mixture[frozenset({second})] == pytest.approx(0.125)
    assert mixture[frozenset({first, second})] == pytest.approx(0.375)


def test_v2_frozen_scenarios_validate_before_outcomes() -> None:
    scenarios = frozen_g1_v2_scenarios()
    assert [scenario.name for scenario in scenarios] == [
        "parallel_three_return",
        "serial_two_cut",
        "hybrid_shared_plus_parallel",
        "fork_serial_vs_parallel",
    ]
    for scenario in scenarios:
        scenario.grid.validate()
        scenario.model.validate(scenario.grid)


def test_v2_lambda_zero_planners_share_matched_failure_outcomes() -> None:
    rows = run_g1_v2_heldout_benchmark(
        weights=(0.0,),
        trials_per_condition=100,
        repetitions=1,
        seed=41,
    )
    assert len(rows) == 52

    grouped: dict[tuple[str, str], list] = {}
    for row in rows:
        grouped.setdefault((row.scenario, row.dependence), []).append(row)

    for condition_rows in grouped.values():
        assert len(condition_rows) == 4
        assert len({row.path_length for row in condition_rows}) == 1
        assert len({row.failures for row in condition_rows}) == 1


def test_v2_true_return_sign_reversal_is_retained() -> None:
    rows = run_g1_v2_heldout_benchmark(
        weights=(0.0,),
        trials_per_condition=10,
        repetitions=1,
        seed=5,
    )
    shortest = {
        (row.scenario, row.dependence): row
        for row in rows
        if row.planner == "shortest"
    }

    assert shortest[
        ("parallel_three_return", "independent")
    ].true_joint_return_probability == pytest.approx(0.875)
    assert shortest[
        ("parallel_three_return", "common_cause")
    ].true_joint_return_probability == pytest.approx(0.5)

    assert shortest[
        ("serial_two_cut", "independent")
    ].true_joint_return_probability == pytest.approx(0.25)
    assert shortest[
        ("serial_two_cut", "common_cause")
    ].true_joint_return_probability == pytest.approx(0.5)
    assert shortest[
        ("serial_two_cut", "anti_correlated")
    ].true_joint_return_probability == pytest.approx(0.0)
