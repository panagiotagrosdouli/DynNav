from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path

from dynnav.activation_pomdp_reference import (
    OneStepActivationDecisionProblem,
    dynnav_belief_one_step_decision,
    exact_one_step_activation_decision,
)
from dynnav.experiments.activation_threshold_frontier import (
    run_activation_threshold_frontier,
)
from dynnav.experiments.causal_effect_sweep import (
    run_confounding_propensity_control,
    run_randomized_ipw_sweep,
)
from dynnav.experiments.noisy_activation_benchmark import (
    ActivationObservationScenario,
)


def _g2_scenarios() -> tuple[ActivationObservationScenario, ...]:
    scenarios: list[ActivationObservationScenario] = []
    for activation in (0.2, 0.5, 0.8):
        for closure in (0.4, 0.8):
            for quality in (0.55, 0.75, 0.95):
                scenarios.append(
                    ActivationObservationScenario(
                        name=(
                            f"calibrated_a{activation:g}_c{closure:g}"
                            f"_q{quality:g}"
                        ),
                        activation_probability=activation,
                        closure_probability=closure,
                        true_sensitivity=quality,
                        true_specificity=quality,
                        assumed_sensitivity=quality,
                        assumed_specificity=quality,
                    )
                )
    scenarios.append(
        ActivationObservationScenario(
            name="misspecified_missed_activation",
            activation_probability=0.5,
            closure_probability=0.8,
            true_sensitivity=0.60,
            true_specificity=0.90,
            assumed_sensitivity=0.95,
            assumed_specificity=0.90,
        )
    )
    return tuple(scenarios)


def _aggregate_g2(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[
        tuple[str, str, float],
        list[dict[str, object]],
    ] = defaultdict(list)
    for row in rows:
        key = (
            str(row["scenario"]),
            str(row["method"]),
            float(row["threshold"]),
        )
        grouped[key].append(row)

    summary: list[dict[str, object]] = []
    for (scenario, method, threshold), items in sorted(grouped.items()):
        n = len(items)
        summary.append(
            {
                "scenario": scenario,
                "method": method,
                "threshold": threshold,
                "repetitions": n,
                "mean_safe_decision_rate": sum(
                    float(item["safe_decision_rate"]) for item in items
                )
                / n,
                "mean_false_safe_rate": sum(
                    float(item["false_safe_rate"]) for item in items
                )
                / n,
                "mean_brier_score": sum(
                    float(item["brier_score"]) for item in items
                )
                / n,
                "mean_empirical_failure_rate": sum(
                    float(item["empirical_failure_rate"]) for item in items
                )
                / n,
            }
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen G2 belief and G4 interventional controls."
    )
    parser.add_argument("--g2-trials", type=int, default=3000)
    parser.add_argument("--g2-repetitions", type=int, default=10)
    parser.add_argument("--g4-repetitions", type=int, default=30)
    parser.add_argument("--g4-confounding-repetitions", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/research_gap_program/g2_g4_publication_controls.json"),
    )
    args = parser.parse_args()
    if min(
        args.g2_trials,
        args.g2_repetitions,
        args.g4_repetitions,
        args.g4_confounding_repetitions,
    ) <= 0:
        raise ValueError("all run sizes must be positive")

    scenarios = _g2_scenarios()
    g2_raw: list[dict[str, object]] = []
    for scenario_index, scenario in enumerate(scenarios):
        for repetition in range(args.g2_repetitions):
            records = run_activation_threshold_frontier(
                scenario,
                thresholds=(0.05, 0.10, 0.20, 0.30, 0.40, 0.50),
                trials=args.g2_trials,
                seed=args.seed + scenario_index * 100_000 + repetition,
            )
            for record in records:
                row = asdict(record)
                row["repetition"] = repetition
                g2_raw.append(row)

    g2_reference: list[dict[str, object]] = []
    max_posterior_error = 0.0
    max_value_error = 0.0
    action_disagreements = 0
    for scenario in scenarios:
        for observed in (False, True):
            for detour_cost in (1.0, 2.0, 4.0):
                problem = OneStepActivationDecisionProblem(
                    activation_probability=scenario.activation_probability,
                    closure_probability=scenario.closure_probability,
                    detector_sensitivity=scenario.assumed_sensitivity,
                    detector_specificity=scenario.assumed_specificity,
                    failure_cost=10.0,
                    detour_cost=detour_cost,
                    continue_cost=0.0,
                )
                reference = exact_one_step_activation_decision(
                    problem,
                    observed_crossing=observed,
                )
                dynnav = dynnav_belief_one_step_decision(
                    problem,
                    observed_crossing=observed,
                )
                posterior_error = abs(
                    reference.posterior_activation_probability
                    - dynnav.posterior_activation_probability
                )
                value_error = abs(reference.value - dynnav.value)
                disagree = reference.action != dynnav.action
                max_posterior_error = max(max_posterior_error, posterior_error)
                max_value_error = max(max_value_error, value_error)
                action_disagreements += int(disagree)
                g2_reference.append(
                    {
                        "scenario": scenario.name,
                        "observed_crossing": observed,
                        "detour_cost": detour_cost,
                        "reference_action": reference.action,
                        "dynnav_action": dynnav.action,
                        "reference_value": reference.value,
                        "dynnav_value": dynnav.value,
                        "posterior_error": posterior_error,
                        "value_error": value_error,
                        "action_disagreement": disagree,
                    }
                )

    g4_randomized = run_randomized_ipw_sweep(
        sample_sizes=(200, 1000, 5000),
        propensities=(0.2, 0.5, 0.8),
        effects=(0.0, 0.1, 0.3, 0.5),
        repetitions=args.g4_repetitions,
        baseline_probability=0.1,
        seed=args.seed,
    )
    corrected, misspecified = run_confounding_propensity_control(
        sample_size=5000,
        repetitions=args.g4_confounding_repetitions,
        confounder_probability=0.5,
        treatment_given_high=0.8,
        treatment_given_low=0.2,
        outcome_given_high=0.8,
        outcome_given_low=0.1,
        seed=args.seed + 5_000_000,
    )

    payload = {
        "metadata": {
            "seed": args.seed,
            "scope": "bounded synthetic G2/G4 publication-control study",
            "g2_trials_per_scenario_repetition": args.g2_trials,
            "g2_repetitions": args.g2_repetitions,
            "g4_randomized_repetitions": args.g4_repetitions,
            "g4_confounding_repetitions": args.g4_confounding_repetitions,
        },
        "G2_frontier_raw": g2_raw,
        "G2_frontier_summary": _aggregate_g2(g2_raw),
        "G2_exact_reference": {
            "rows": g2_reference,
            "max_posterior_error": max_posterior_error,
            "max_value_error": max_value_error,
            "action_disagreements": action_disagreements,
        },
        "G4_randomized_sweep": [asdict(row) for row in g4_randomized],
        "G4_confounding_control": {
            "correct_record_propensity": asdict(corrected),
            "misspecified_marginal_propensity": asdict(misspecified),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
