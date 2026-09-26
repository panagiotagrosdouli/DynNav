from __future__ import annotations

import pytest

from dynnav.activation_belief import ActivationBelief
from dynnav.causal_trigger_discovery import TriggerOutcomeRecord, estimate_ipw_trigger_effect
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.distributional_recoverability import (
    PairwiseClosureConstraint,
    ProbabilityInterval,
    TopologyAmbiguitySet,
    robust_safe_return_bounds,
)
from dynnav.history_compression import build_hazard_event_quotient
from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    SafeProbeCandidate,
    select_safe_information_probe,
)
from dynnav.planners.grid_map import GridMap


def _parallel_corridors():
    free = {(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2), (0, 1), (2, 1)}
    obstacles = {(x, y) for x in range(3) for y in range(3) if (x, y) not in free}
    return GridMap.from_obstacles(3, 3, obstacles=obstacles), (2, 1), {(0, 1)}


def test_g1_fixed_marginals_leave_large_dependence_ambiguity() -> None:
    grid, current, safe = _parallel_corridors()
    ambiguity = TopologyAmbiguitySet(
        marginals={
            (1, 0): ProbabilityInterval(0.5, 0.5),
            (1, 2): ProbabilityInterval(0.5, 0.5),
        }
    )
    bounds = robust_safe_return_bounds(grid, current, safe, ambiguity)
    assert bounds.lower == pytest.approx(0.5)
    assert bounds.upper == pytest.approx(1.0)


def test_g1_pairwise_information_identifies_independent_reliability() -> None:
    grid, current, safe = _parallel_corridors()
    ambiguity = TopologyAmbiguitySet(
        marginals={
            (1, 0): ProbabilityInterval(0.5, 0.5),
            (1, 2): ProbabilityInterval(0.5, 0.5),
        },
        pairwise=(
            PairwiseClosureConstraint(
                (1, 0),
                (1, 2),
                ProbabilityInterval(0.25, 0.25),
            ),
        ),
    )
    bounds = robust_safe_return_bounds(grid, current, safe, ambiguity)
    assert bounds.lower == pytest.approx(0.75)
    assert bounds.upper == pytest.approx(0.75)


def test_g2_bayes_update_retains_activation_uncertainty() -> None:
    posterior = ActivationBelief.certain_inactive().update_after_trigger_attempt(
        0,
        execution_probability=0.5,
        observed_crossing=True,
        detection_sensitivity=0.8,
        detection_specificity=0.8,
    )
    active_probability = sum(
        probability
        for active, probability in posterior.probability_by_active_set.items()
        if 0 in active
    )
    assert active_probability == pytest.approx(0.8)


def test_g3_non_exposure_does_not_fake_calibration_data() -> None:
    prior = BetaClosurePosterior(1.0, 1.0)
    unchanged = prior.update(exposed=False)
    updated = prior.update(exposed=True, closure_observed=True)
    assert unchanged == prior
    assert updated.exposures == 1
    assert updated.closures == 1
    assert updated.mean > prior.mean


def test_g3_safe_probe_rejects_informative_but_unsafe_trigger() -> None:
    posteriors = {
        0: BetaClosurePosterior(1.0, 1.0),
        1: BetaClosurePosterior(1.0, 1.0),
    }
    decision = select_safe_information_probe(
        posteriors,
        (
            SafeProbeCandidate(0, predicted_return_probability=0.6, traversal_cost=1.0),
            SafeProbeCandidate(1, predicted_return_probability=0.95, traversal_cost=2.0),
        ),
        minimum_return_probability=0.9,
    )
    assert decision.hazard_index == 1


def test_g4_ipw_recovers_randomized_trigger_effect_in_constructed_data() -> None:
    records = [
        TriggerOutcomeRecord("t0", "c0", True, True, 0.5)
        for _ in range(4)
    ] + [
        TriggerOutcomeRecord("t0", "c0", False, False, 0.5)
        for _ in range(4)
    ]
    estimate = estimate_ipw_trigger_effect(records, trigger_id="t0", closure_id="c0")
    assert estimate.ate == pytest.approx(1.0)
    assert estimate.treated_mean == pytest.approx(1.0)
    assert estimate.control_mean == pytest.approx(0.0)


def test_g5_duplicate_trigger_semantics_compress_exactly() -> None:
    model = CommitmentHazardModel(
        (
            CommitmentClosure(((0, 0), (1, 0)), (2, 0), 0.5),
            CommitmentClosure(((0, 1), (1, 1)), (2, 0), 0.5),
            CommitmentClosure(((1, 1), (2, 1)), (2, 2), 0.7),
        )
    )
    quotient = build_hazard_event_quotient(model)
    assert quotient.hazard_count == 3
    assert quotient.event_count == 2
    assert quotient.compress_active_indices(frozenset({0})) == quotient.compress_active_indices(
        frozenset({1})
    )
    assert quotient.worst_case_state_count_reduction == 4
