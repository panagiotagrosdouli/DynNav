from __future__ import annotations

from dynnav.empirical_topology_ambiguity import (
    ClosureObservation,
    fit_empirical_topology_ambiguity,
)
from dynnav.experiments.empirical_ambiguity_route_benchmark import (
    run_empirical_ambiguity_route_benchmark,
)


def test_empirical_ambiguity_intervals_cover_constructed_half_probability() -> None:
    hazards = ((1, 0), (1, 2))
    observations = []
    for index in range(100):
        closed = set()
        if index % 2 == 0:
            closed.add(hazards[0])
        if index % 4 < 2:
            closed.add(hazards[1])
        observations.append(ClosureObservation(frozenset(closed)))

    fit = fit_empirical_topology_ambiguity(
        observations,
        hazards,
        family_confidence=0.95,
        include_pairwise=True,
    )

    first = fit.ambiguity.marginals[hazards[0]]
    second = fit.ambiguity.marginals[hazards[1]]
    assert first.lower <= 0.5 <= first.upper
    assert second.lower <= 0.5 <= second.upper

    pair = fit.ambiguity.pairwise[0].probability
    assert pair.lower <= 0.25 <= pair.upper


def test_finite_data_benchmark_retains_dependence_conditions() -> None:
    rows = run_empirical_ambiguity_route_benchmark(
        training_sizes=(50,),
        repetitions=3,
        seed=101,
    )
    assert len(rows) == 3 * 1 * 3 * 3
    assert {row.dependence for row in rows} == {
        "independent",
        "common_cause",
        "anti_correlated",
    }
    assert {row.method for row in rows} == {
        "plugin_independence",
        "empirical_marginal_robust",
        "empirical_pairwise_robust",
    }

    common_pairwise = [
        row
        for row in rows
        if row.dependence == "common_cause"
        and row.method == "empirical_pairwise_robust"
    ]
    assert all(row.true_failure_probability in (0.0, 0.5) for row in common_pairwise)
