"""Unified bounded research benchmark for DynNav gaps G1-G5.

The runner is intentionally small enough for CI. It produces machine-readable
mechanism evidence and negative controls; it does not replace the larger
predeclared ROS/Gazebo or held-out studies in RESEARCH_GAPS_G1_G5.md.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path

from dynnav.causal_trigger_discovery import (
    TriggerOutcomeRecord,
    estimate_ipw_trigger_effect,
)
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.distributional_recoverability import (
    PairwiseClosureConstraint,
    ProbabilityInterval,
    TopologyAmbiguitySet,
    robust_safe_return_bounds,
)
from dynnav.experiments.activation_threshold_frontier import (
    run_activation_threshold_frontier,
)
from dynnav.experiments.causal_graph_benchmark import (
    run_causal_graph_recovery_benchmark,
)
from dynnav.experiments.dependence_shift_benchmark import (
    run_dependence_shift_benchmark,
)
from dynnav.experiments.history_compression_benchmark import (
    records_as_dicts as compression_records_as_dicts,
    run_history_compression_scaling,
)
from dynnav.experiments.noisy_activation_benchmark import ActivationObservationScenario
from dynnav.experiments.online_calibration_benchmark import (
    records_as_dicts as calibration_records_as_dicts,
    run_online_calibration_benchmark,
)
from dynnav.history_compression import build_hazard_event_quotient
from dynnav.online_hazard_learning import BetaClosurePosterior
from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_belief import (
    TopologyHazardBelief,
    exact_safe_return_probability,
)


def _parallel_corridors(
    corridor_count: int,
) -> tuple[GridMap, tuple[int, int], set[tuple[int, int]], tuple[tuple[int, int], ...]]:
    if corridor_count < 1:
        raise ValueError("corridor_count must be positive")
    height = 2 * corridor_count - 1
    free = {(0, y) for y in range(height)}
    free.update({(2, y) for y in range(height)})
    hazard_cells = tuple((1, 2 * index) for index in range(corridor_count))
    free.update(hazard_cells)
    obstacles = {
        (x, y)
        for x in range(3)
        for y in range(height)
        if (x, y) not in free
    }
    middle = height // 2
    return (
        GridMap.from_obstacles(3, height, obstacles=obstacles),
        (2, middle),
        {(0, middle)},
        hazard_cells,
    )


def _g1() -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for corridor_count in (2, 3, 4, 5):
        grid, current, safe, hazard_cells = _parallel_corridors(corridor_count)
        for probability in (0.2, 0.5, 0.8):
            marginals = {
                cell: ProbabilityInterval(probability, probability)
                for cell in hazard_cells
            }
            ambiguity = TopologyAmbiguitySet(marginals=marginals)
            bounds = robust_safe_return_bounds(grid, current, safe, ambiguity)
            independent = exact_safe_return_probability(
                grid,
                current,
                safe,
                TopologyHazardBelief(
                    {cell: probability for cell in hazard_cells}
                ),
            )
            rows.append(
                {
                    "corridors": corridor_count,
                    "marginal_probability": probability,
                    "independent_return": independent,
                    "worst_case_return": bounds.lower,
                    "best_case_return": bounds.upper,
                    "ambiguity_width": bounds.upper - bounds.lower,
                    "common_cause_return": 1.0 - probability,
                }
            )

    grid, current, safe, hazard_cells = _parallel_corridors(2)
    identified = robust_safe_return_bounds(
        grid,
        current,
        safe,
        TopologyAmbiguitySet(
            marginals={
                cell: ProbabilityInterval(0.5, 0.5)
                for cell in hazard_cells
            },
            pairwise=(
                PairwiseClosureConstraint(
                    hazard_cells[0],
                    hazard_cells[1],
                    ProbabilityInterval(0.25, 0.25),
                ),
            ),
        ),
    )
    rows.append(
        {
            "corridors": 2,
            "marginal_probability": 0.5,
            "independent_return": 0.75,
            "worst_case_return": identified.lower,
            "best_case_return": identified.upper,
            "ambiguity_width": identified.upper - identified.lower,
            "common_cause_return": 0.5,
        }
    )
    return rows


def _g2(*, trials: int, seed: int) -> list[dict[str, object]]:
    scenarios = (
        ActivationObservationScenario(
            "calibrated_informative",
            activation_probability=0.5,
            closure_probability=0.8,
            true_sensitivity=0.9,
            true_specificity=0.9,
            assumed_sensitivity=0.9,
            assumed_specificity=0.9,
        ),
        ActivationObservationScenario(
            "missed_activation_miscalibrated",
            activation_probability=0.5,
            closure_probability=0.8,
            true_sensitivity=0.6,
            true_specificity=0.9,
            assumed_sensitivity=0.95,
            assumed_specificity=0.9,
        ),
    )
    rows: list[dict[str, object]] = []
    for index, scenario in enumerate(scenarios):
        records = run_activation_threshold_frontier(
            scenario,
            thresholds=(0.05, 0.10, 0.20, 0.30, 0.40, 0.50),
            trials=trials,
            seed=seed + index,
        )
        rows.extend(asdict(record) for record in records)
    return rows


def _posterior_summary(
    name: str,
    posterior: BetaClosurePosterior,
    *,
    opportunities: int,
) -> dict[str, float | int | str]:
    lower, upper = posterior.credible_interval(0.95)
    return {
        "policy": name,
        "opportunities": opportunities,
        "exposures": posterior.exposures,
        "closures": posterior.closures,
        "posterior_mean": posterior.mean,
        "posterior_variance": posterior.variance,
        "credible_lower": lower,
        "credible_upper": upper,
    }


def _g3(*, trials: int, seed: int) -> list[dict[str, float | int | str]]:
    opportunities = min(trials, 5_000)
    true_probability = 0.7
    rng = random.Random(seed)
    latent_closures = [
        rng.random() < true_probability
        for _ in range(opportunities)
    ]

    always_avoid = BetaClosurePosterior(1.0, 3.0)
    always_probe = BetaClosurePosterior(1.0, 3.0)
    half_probe = BetaClosurePosterior(1.0, 3.0)
    half_probe_naive = BetaClosurePosterior(1.0, 3.0)

    for step, closure in enumerate(latent_closures):
        always_avoid = always_avoid.update(exposed=False)
        always_probe = always_probe.update(
            exposed=True,
            closure_observed=closure,
        )

        exposed = step % 2 == 0
        half_probe = half_probe.update(
            exposed=exposed,
            closure_observed=closure if exposed else False,
        )
        # Deliberately wrong logger: unexposed opportunities are counted as
        # observed non-closures. This is the G3 negative control.
        half_probe_naive = half_probe_naive.update(
            exposed=True,
            closure_observed=closure if exposed else False,
        )

    rows = [
        _posterior_summary("always_avoid", always_avoid, opportunities=opportunities),
        _posterior_summary("always_probe", always_probe, opportunities=opportunities),
        _posterior_summary("half_probe_correct", half_probe, opportunities=opportunities),
        _posterior_summary(
            "half_probe_naive_unexposed_as_open",
            half_probe_naive,
            opportunities=opportunities,
        ),
    ]
    for row in rows:
        row["true_probability"] = true_probability
        row["absolute_error"] = abs(float(row["posterior_mean"]) - true_probability)
    return rows


def _simulate_effect_records(
    *,
    rng: random.Random,
    trials: int,
    trigger_id: str,
    treated_probability: float,
    control_probability: float,
) -> list[TriggerOutcomeRecord]:
    records: list[TriggerOutcomeRecord] = []
    for _ in range(trials):
        propensity = 0.5
        executed = rng.random() < propensity
        probability = treated_probability if executed else control_probability
        records.append(
            TriggerOutcomeRecord(
                trigger_id,
                "return_cut",
                executed,
                rng.random() < probability,
                propensity,
            )
        )
    return records


def _g4(*, trials: int, seed: int) -> list[dict[str, float | int | str]]:
    rng = random.Random(seed)
    positive = _simulate_effect_records(
        rng=rng,
        trials=trials,
        trigger_id="positive_trigger",
        treated_probability=0.75,
        control_probability=0.15,
    )
    null = _simulate_effect_records(
        rng=rng,
        trials=trials,
        trigger_id="null_trigger",
        treated_probability=0.30,
        control_probability=0.30,
    )

    confounded: list[TriggerOutcomeRecord] = []
    for _ in range(trials):
        severe_context = rng.random() < 0.5
        actual_propensity = 0.8 if severe_context else 0.2
        executed = rng.random() < actual_propensity
        outcome_probability = 0.8 if severe_context else 0.1
        confounded.append(
            TriggerOutcomeRecord(
                "confounded_observational_trigger",
                "return_cut",
                executed,
                rng.random() < outcome_probability,
                0.5,
            )
        )

    datasets = (
        ("randomized_positive", positive, "positive_trigger", 0.60),
        ("randomized_null", null, "null_trigger", 0.0),
        (
            "hidden_confounding_negative_control",
            confounded,
            "confounded_observational_trigger",
            0.0,
        ),
    )
    rows: list[dict[str, float | int | str]] = []
    for name, records, trigger_id, true_ate in datasets:
        estimate = estimate_ipw_trigger_effect(
            records,
            trigger_id=trigger_id,
            closure_id="return_cut",
        )
        lower, upper = estimate.approximate_95_interval
        rows.append(
            {
                "condition": name,
                "estimate": estimate.ate,
                "standard_error": estimate.standard_error,
                "approximate_95_lower": lower,
                "approximate_95_upper": upper,
                "treated_count": estimate.treated_count,
                "control_count": estimate.control_count,
                "true_ate": true_ate,
            }
        )
    return rows


def _g5() -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for hazard_count in (2, 4, 8, 12):
        closures = tuple(
            CommitmentClosure(
                ((index, 0), (index + 1, 0)),
                (100 + (index % 2), 0),
                0.5,
            )
            for index in range(hazard_count)
        )
        quotient = build_hazard_event_quotient(CommitmentHazardModel(closures))
        rows.append(
            {
                "raw_hazard_count": quotient.hazard_count,
                "closure_event_count": quotient.event_count,
                "raw_subset_state_count": 2 ** quotient.hazard_count,
                "quotient_subset_state_count": 2 ** quotient.event_count,
                "state_count_reduction": quotient.worst_case_state_count_reduction,
            }
        )
    return rows


def run_research_gap_program(
    *,
    trials: int = 10_000,
    seed: int = 20260925,
) -> dict[str, object]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    return {
        "metadata": {
            "seed": seed,
            "trials_for_stochastic_sections": trials,
            "scope": "bounded mechanism study; not deployment efficacy",
        },
        "G1_dependence_ambiguity": _g1(),
        "G1_dependence_shift_execution": [
            asdict(record)
            for record in run_dependence_shift_benchmark(
                trials=trials,
                seed=seed + 5,
            )
        ],
        "G2_activation_belief_frontier": _g2(trials=trials, seed=seed + 10),
        "G3_logging_bias_control": _g3(trials=trials, seed=seed + 20),
        "G3_online_policy_benchmark": calibration_records_as_dicts(
            run_online_calibration_benchmark(
                opportunities=min(trials, 5_000),
                seed=seed + 21,
            )
        ),
        "G4_interventional_trigger_effect": _g4(trials=trials, seed=seed + 30),
        "G4_causal_graph_recovery": asdict(
            run_causal_graph_recovery_benchmark(
                trials_per_pair=max(200, min(trials, 2_000)),
                seed=seed + 31,
            )
        ),
        "G5_history_compression_counts": _g5(),
        "G5_search_scaling": compression_records_as_dicts(
            run_history_compression_scaling()
        ),
    }


def write_research_gap_artifact(
    result: dict[str, object],
    output_path: str | Path,
) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
