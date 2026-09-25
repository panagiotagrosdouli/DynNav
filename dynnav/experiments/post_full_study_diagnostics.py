"""Post-full-study exploratory diagnostics for G1, G3 and G5.

These diagnostics were designed after inspecting the frozen V1 full-study
artifact. They must not be mixed with the confirmatory V1 claim gate.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from dynnav.experiments.empirical_ambiguity_route_benchmark import (
    run_empirical_ambiguity_route_benchmark,
)
from dynnav.experiments.history_compression_state_space import (
    run_reachable_state_space_scaling,
)
from dynnav.experiments.risk_budget_learning_benchmark import (
    run_risk_budget_learning_benchmark,
)
from dynnav.experiments.safe_learning_lockout_benchmark import (
    run_safe_learning_lockout_benchmark,
)
from dynnav.experiments.topology_dependence_control import (
    run_topology_dependence_control,
)
from dynnav.experiments.topology_interaction_survey import (
    run_topology_interaction_survey,
)


def run_post_full_study_diagnostics(
    *,
    opportunities: int = 2_000,
    seed: int = 20260925,
) -> dict[str, object]:
    """Run exploratory topology, learning-lockout and state-space diagnostics."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")

    g1 = [asdict(row) for row in run_topology_dependence_control()]
    g1_survey = [
        asdict(row)
        for row in run_topology_interaction_survey(
            accepted_maps=40,
            obstacle_probability=0.30,
            seed=seed,
        )
    ]
    g1_empirical = [
        asdict(row)
        for row in run_empirical_ambiguity_route_benchmark(
            training_sizes=(20, 50, 100, 500),
            repetitions=20,
            family_confidence=0.95,
            seed=seed + 20_000,
        )
    ]

    g3_lockout: list[dict[str, object]] = []
    condition = 0
    for true_probability in (0.1, 0.3, 0.5, 0.7, 0.9):
        for minimum_return in (0.5, 0.7, 0.9):
            for confidence in (0.80, 0.90, 0.95):
                rows = run_safe_learning_lockout_benchmark(
                    opportunities=opportunities,
                    true_closure_probability=true_probability,
                    minimum_return_probability=minimum_return,
                    confidence=confidence,
                    seed=seed + 100 + condition,
                )
                g3_lockout.extend(asdict(row) for row in rows)
                condition += 1

    g3_budget: list[dict[str, object]] = []
    condition = 0
    for true_probability in (0.1, 0.3, 0.5, 0.7):
        for minimum_return in (0.5, 0.7, 0.9):
            rows = run_risk_budget_learning_benchmark(
                opportunities=opportunities,
                true_closure_probability=true_probability,
                minimum_return_probability=minimum_return,
                confidence=0.90,
                budgets=(5.0, 20.0, 50.0),
                seed=seed + 5000 + condition,
            )
            g3_budget.extend(asdict(row) for row in rows)
            condition += 1

    g5 = [
        asdict(row)
        for row in run_reachable_state_space_scaling(
            module_counts=(1, 2, 3, 4, 5, 6)
        )
    ]

    return {
        "metadata": {
            "seed": seed,
            "opportunities_per_g3_condition": opportunities,
            "scope": (
                "post-full-study exploratory diagnostics; "
                "not part of frozen EXPERIMENT_PROTOCOL_G1_G5_V1"
            ),
        },
        "G1_topology_dependence_sign_reversal": g1,
        "G1_held_out_topology_interaction_survey": g1_survey,
        "G1_finite_data_ambiguity_routes": g1_empirical,
        "G3_safe_learning_lockout": g3_lockout,
        "G3_risk_budget_deadlock_breaker": g3_budget,
        "G5_full_reachable_state_space": g5,
    }


def write_post_full_study_diagnostics(
    result: dict[str, object],
    output_path: str | Path,
) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
