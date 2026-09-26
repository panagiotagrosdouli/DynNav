from __future__ import annotations

from dynnav.online_hazard_learning import BetaClosurePosterior
from dynnav.safe_learning_lockout_theory import (
    strict_credible_gate_cold_start_lockout,
)


def test_strict_credible_gate_has_absorbing_cold_start_lockout() -> None:
    result = strict_credible_gate_cold_start_lockout(
        BetaClosurePosterior(1.0, 3.0),
        minimum_return_probability=0.7,
        confidence=0.90,
    )
    assert result.locked
    assert not result.initial_allowed
    assert result.posterior_invariant_without_exposure


def test_lockout_does_not_apply_when_prior_is_already_admissible() -> None:
    result = strict_credible_gate_cold_start_lockout(
        BetaClosurePosterior(1.0, 20.0),
        minimum_return_probability=0.5,
        confidence=0.90,
    )
    assert not result.locked
    assert result.initial_allowed
