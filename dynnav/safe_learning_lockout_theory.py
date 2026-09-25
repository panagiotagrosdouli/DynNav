"""Cold-start lockout proposition for exposure-gated hazard learning.

If (i) the posterior state can change only after trigger exposure, and
(ii) a deterministic strict safety gate rejects exposure at the initial
posterior, then the posterior remains invariant forever and the gate never
opens. This is a structural identifiability deadlock, not a finite-sample
accident.

The helper below records the proposition for the Beta critical-trigger model
used by DynNav's G3 diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    credible_safe_probe_allowed,
)


@dataclass(frozen=True)
class ColdStartLockoutResult:
    locked: bool
    initial_allowed: bool
    posterior_invariant_without_exposure: bool
    reason: str


def strict_credible_gate_cold_start_lockout(
    prior: BetaClosurePosterior,
    *,
    minimum_return_probability: float,
    confidence: float = 0.90,
) -> ColdStartLockoutResult:
    """Diagnose the deterministic cold-start lockout condition.

    Under the repository exposure-only update semantics, updating with
    exposed=False leaves the posterior unchanged. Therefore if the strict
    credible gate rejects the prior once, repeated no-exposure decisions
    cannot create new information and the rejection is absorbing.
    """

    prior.validate()
    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")

    initial_allowed = credible_safe_probe_allowed(
        prior,
        minimum_return_probability=minimum_return_probability,
        confidence=confidence,
    )
    unchanged = prior.update(exposed=False) == prior
    locked = (not initial_allowed) and unchanged
    return ColdStartLockoutResult(
        locked=locked,
        initial_allowed=initial_allowed,
        posterior_invariant_without_exposure=unchanged,
        reason=(
            "strict gate rejects the invariant no-exposure posterior"
            if locked
            else "cold-start lockout condition does not hold"
        ),
    )
