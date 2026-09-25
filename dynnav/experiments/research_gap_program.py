"""Unified bounded research benchmark for DynNav gaps G1-G5.

The runner is intentionally small enough for CI.  It establishes mechanism
checks and produces machine-readable outputs; it does not replace the larger
predeclared ROS/Gazebo or held-out studies described in RESEARCH_GAPS_G1_G5.md.
"""

from __future__ import annotations

import json
import random
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
from dynnav.experiments.noisy_activation_benchmark import (
    ActivationObservationScenario,
    run_noisy_activation_benchmark,
)
from dynnav.history_compression import build_hazard_event_quotient
from dynnav.online_hazard_learning import BetaClosurePosterior
from dynnav.planners.grid_map import GridMap


def _parallel_corridors():
    free = {(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2), (0, 1), (2, 1)}
    obstacles = {(x, y) for x in range(3) for y in range(3) if (x, y) not in free}
    return GridMap.from_obstacles(3, 3, obstacles=obstacles), (2, 1), {(0, 1)}


def _g1() -> dict[str, float]:
    grid, current, safe = _parallel_corridors()
    marginal_only = TopologyAmbiguitySet(
        marginals={
            (1, 0): ProbabilityInterval(0.5, 0.5),
            (1, 2): ProbabilityInterval(0.5, 0.5),
        }
    )
    with_pairwise = TopologyAmbiguitySet(
        marginals=marginal_only.marginals,
        pairwise=(
            PairwiseClosureConstraint(
                (1, 0),
                (1, 2),
                ProbabilityInterval(0.25, 0.25),
            ),
        ),
    )
    unconstrained = robust_safe_return_bounds(grid, current, safe, marginal_only)
    identified = robust_safe_return_bounds(grid, current, safe, with_pairwise)
    return {
        "marginal_only_worst_case_return": unconstrained.lower,
        "marginal_only_best_case_return": unconstrained.upper,
        "dependence_ambiguity_width": unconstrained.upper - unconstrained.lower,
        "identified_pairwise_return": identified.lower,
    }


def _g2(*, trials: int, seed: int) -> dict[str, float]:
    scenario = ActivationObservationScenario(
        "gap_program_miscalibration",
        activation_probability=0.5,
        closure_probability=0.8,
        true_sensitivity=0.6,
        true_specificity=0.9,
        assumed_sensitivity=0.95,
        assumed_specificity=0.9,
    )
    records = run_noisy_activation_benchmark(
        scenarios=(scenario,),
        trials=trials,
        seed=seed,
    )
    by_method = {record.method: record for record in records}
    return {
        "bayes_brier": by_method["bayes_posterior"].brier_score,
        "bayes_false_safe_rate": by_method["bayes_posterior"].false_safe_rate_at_0_2,
        "detector_as_truth_brier": by_method["detector_as_truth"].brier_score,
        "detector_as_truth_false_safe_rate": by_method[
            "detector_as_truth"
        ].false_safe_rate_at_0_2,
    }


def _g3(*, trials: int, seed: int) -> dict[str, float | int]:
    rng = random.Random(seed)
    true_probability = 0.7
    posterior = BetaClosurePosterior(1.0, 1.0)
    # The policy only probes on alternating opportunities.  Non-exposure must
    # not be laundered into negative closure evidence.
    opportunities = trials
    exposures = 0
    for step in range(opportunities):
        exposed = step % 2 == 0
        if exposed:
            exposures += 1
            posterior = posterior.update(
                exposed=True,
                closure_observed=rng.random() < true_probability,
            )
        else:
            posterior = posterior.update(exposed=False)
    lo, hi = posterior.credible_interval(0.95)
    return {
        "opportunities": opportunities,
        "exposures": exposures,
        "posterior_mean": posterior.mean,
        "posterior_variance": posterior.variance,
        "credible_lower": lo,
        "credible_upper": hi,
        "true_probability": true_probability,
    }


def _g4(*, trials: int, seed: int) -> dict[str, float | int]:
    rng = random.Random(seed)
    records: list[TriggerOutcomeRecord] = []
    for _ in range(trials):
        propensity = 0.5
        executed = rng.random() < propensity
        closure_probability = 0.75 if executed else 0.15
        records.append(
            TriggerOutcomeRecord(
                "candidate_trigger",
                "return_cut",
                executed,
                rng.random() < closure_probability,
                propensity,
            )
        )
    estimate = estimate_ipw_trigger_effect(
        records,
        trigger_id="candidate_trigger",
        closure_id="return_cut",
    )
    lo, hi = estimate.approximate_95_interval
    return {
        "ate": estimate.ate,
        "standard_error": estimate.standard_error,
        "approximate_95_lower": lo,
        "approximate_95_upper": hi,
        "treated_count": estimate.treated_count,
        "control_count": estimate.control_count,
        "true_ate": 0.60,
    }


def _g5() -> dict[str, int]:
    model = CommitmentHazardModel(
        (
            CommitmentClosure(((0, 0), (1, 0)), (2, 0), 0.5),
            CommitmentClosure(((0, 1), (1, 1)), (2, 0), 0.5),
            CommitmentClosure(((0, 2), (1, 2)), (2, 0), 0.5),
            CommitmentClosure(((1, 0), (2, 0)), (2, 2), 0.7),
        )
    )
    quotient = build_hazard_event_quotient(model)
    return {
        "raw_hazard_count": quotient.hazard_count,
        "closure_event_count": quotient.event_count,
        "raw_subset_state_count": 2 ** quotient.hazard_count,
        "quotient_subset_state_count": 2 ** quotient.event_count,
        "state_count_reduction": quotient.worst_case_state_count_reduction,
    }


def run_research_gap_program(*, trials: int = 10_000, seed: int = 20260925) -> dict[str, object]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    return {
        "metadata": {
            "seed": seed,
            "trials_for_stochastic_sections": trials,
            "scope": "bounded mechanism/CI study; not deployment efficacy",
        },
        "G1_dependence_ambiguity": _g1(),
        "G2_activation_belief": _g2(trials=trials, seed=seed + 10),
        "G3_online_calibration": _g3(trials=trials, seed=seed + 20),
        "G4_interventional_trigger_effect": _g4(trials=trials, seed=seed + 30),
        "G5_history_compression": _g5(),
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
