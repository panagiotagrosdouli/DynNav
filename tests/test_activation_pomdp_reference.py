from __future__ import annotations

import pytest

from dynnav.activation_pomdp_reference import (
    OneStepActivationDecisionProblem,
    direct_activation_posterior,
    dynnav_belief_one_step_decision,
    exact_one_step_activation_decision,
)


@pytest.mark.parametrize("observed", [False, True])
def test_dynnav_activation_belief_matches_closed_form_pomdp_posterior(
    observed: bool,
) -> None:
    problem = OneStepActivationDecisionProblem(
        activation_probability=0.4,
        closure_probability=0.8,
        detector_sensitivity=0.85,
        detector_specificity=0.9,
        failure_cost=10.0,
        detour_cost=2.0,
    )
    closed_form = direct_activation_posterior(
        problem,
        observed_crossing=observed,
    )
    dynnav = dynnav_belief_one_step_decision(
        problem,
        observed_crossing=observed,
    )
    assert dynnav.posterior_activation_probability == pytest.approx(closed_form)


@pytest.mark.parametrize("observed", [False, True])
def test_dynnav_belief_decision_matches_exact_one_step_pomdp(
    observed: bool,
) -> None:
    problem = OneStepActivationDecisionProblem(
        activation_probability=0.5,
        closure_probability=0.8,
        detector_sensitivity=0.9,
        detector_specificity=0.9,
        failure_cost=8.0,
        detour_cost=2.5,
        continue_cost=0.2,
    )
    reference = exact_one_step_activation_decision(
        problem,
        observed_crossing=observed,
    )
    dynnav = dynnav_belief_one_step_decision(
        problem,
        observed_crossing=observed,
    )
    assert dynnav.action == reference.action
    assert dynnav.value == pytest.approx(reference.value)
    assert dynnav.posterior_failure_probability == pytest.approx(
        reference.posterior_failure_probability
    )


def test_informative_positive_detection_can_flip_decision_to_detour() -> None:
    problem = OneStepActivationDecisionProblem(
        activation_probability=0.2,
        closure_probability=0.9,
        detector_sensitivity=0.95,
        detector_specificity=0.95,
        failure_cost=10.0,
        detour_cost=2.0,
    )
    negative = exact_one_step_activation_decision(
        problem,
        observed_crossing=False,
    )
    positive = exact_one_step_activation_decision(
        problem,
        observed_crossing=True,
    )
    assert negative.action == "continue"
    assert positive.action == "detour"


def test_uninformative_detector_leaves_decision_equal_to_prior_decision() -> None:
    problem = OneStepActivationDecisionProblem(
        activation_probability=0.3,
        closure_probability=0.5,
        detector_sensitivity=0.5,
        detector_specificity=0.5,
        failure_cost=4.0,
        detour_cost=1.0,
    )
    negative = exact_one_step_activation_decision(
        problem,
        observed_crossing=False,
    )
    positive = exact_one_step_activation_decision(
        problem,
        observed_crossing=True,
    )
    assert negative.posterior_activation_probability == pytest.approx(0.3)
    assert positive.posterior_activation_probability == pytest.approx(0.3)
    assert negative.action == positive.action
