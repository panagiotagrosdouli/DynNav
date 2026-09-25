from __future__ import annotations

from dynnav.experiments.unavoidable_history_benchmark import (
    frozen_unavoidable_scenarios,
    minimum_activated_hazards_to_goal,
    run_unavoidable_history_benchmark,
    summarize_unavoidable_history,
    unavoidable_choice_world,
)


def test_single_module_has_no_trigger_free_route() -> None:
    scenario = unavoidable_choice_world(
        direct_probabilities=(0.8,),
        detour_probabilities=(0.2,),
        detour_depths=(1,),
        detour_directions=(-1,),
        name="single",
    )

    assert minimum_activated_hazards_to_goal(scenario) == 1


def test_multiple_modules_require_one_activation_per_module() -> None:
    scenario = unavoidable_choice_world(
        direct_probabilities=(0.8, 0.2, 0.7),
        detour_probabilities=(0.2, 0.7, 0.3),
        detour_depths=(1, 2, 1),
        detour_directions=(-1, 1, -1),
        name="three",
    )

    assert minimum_activated_hazards_to_goal(scenario) == 3


def test_frozen_generator_is_reproducible() -> None:
    left = frozen_unavoidable_scenarios(seed=20260925, count=4)
    right = frozen_unavoidable_scenarios(seed=20260925, count=4)

    assert [
        (
            scenario.name,
            scenario.module_count,
            scenario.detour_depths,
            scenario.detour_directions,
            scenario.model.closures,
        )
        for scenario in left
    ] == [
        (
            scenario.name,
            scenario.module_count,
            scenario.detour_depths,
            scenario.detour_directions,
            scenario.model.closures,
        )
        for scenario in right
    ]


def test_smoke_suite_includes_exact_state_only_and_nonzero_history_hazards() -> None:
    scenarios = frozen_unavoidable_scenarios(count=2)
    records = run_unavoidable_history_benchmark(
        scenarios=scenarios,
        seeds=tuple(range(8)),
        recoverability_weight=8.0,
    )
    summary = summarize_unavoidable_history(records)

    for scenario in scenarios:
        block = summary[scenario.name]
        assert "state_only_exact" in block
        assert "history_exact" in block
        assert block["history_exact"]["activated_closure_count"] >= scenario.module_count
        assert block["state_only_exact"]["trials"] == 8
