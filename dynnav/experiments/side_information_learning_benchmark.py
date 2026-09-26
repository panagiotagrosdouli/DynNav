"""G3 side-information benchmark for breaking target-exposure lockout.

A target trigger may be too risky to expose under a strict credible-return
gate. This module studies whether a separate safe sentinel trigger can provide
information without exposing the target.

The sentinel-transfer policy assumes the sentinel and target share one
Bernoulli closure parameter. That exchangeability assumption is explicit and
is stress-tested with misspecified sentinel probabilities.

This is an identifiability/assumption study, not a deployment-safety claim.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    credible_safe_probe_allowed,
)


@dataclass(frozen=True)
class SideInformationLearningRecord:
    policy: str
    true_target_probability: float
    true_sentinel_probability: float
    minimum_return_probability: float
    confidence: float
    opportunities: int
    sentinel_observations: int
    target_exposures: int
    target_failures: int
    false_safe_exposures: int
    posterior_mean: float
    absolute_error: float
    first_target_exposure_step: int | None


def _target_is_truly_safe(
    true_target_probability: float,
    minimum_return_probability: float,
) -> bool:
    return 1.0 - true_target_probability >= minimum_return_probability


def run_side_information_learning_benchmark(
    *,
    opportunities: int = 2_000,
    true_target_probability: float = 0.3,
    true_sentinel_probability: float | None = None,
    minimum_return_probability: float = 0.7,
    confidence: float = 0.90,
    seed: int = 0,
) -> list[SideInformationLearningRecord]:
    """Compare target-only gating, sentinel transfer and a target oracle.

    The sentinel is observed every opportunity and is operationally safe for
    the simplified return model. Under the shared-parameter model, each
    sentinel outcome updates the posterior used to gate target exposure.

    If the sentinel and target probabilities differ, that is a deliberate
    transfer-model misspecification control.
    """

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")
    if not 0.0 <= true_target_probability <= 1.0:
        raise ValueError("true_target_probability must be in [0, 1]")
    sentinel_probability = (
        true_target_probability
        if true_sentinel_probability is None
        else true_sentinel_probability
    )
    if not 0.0 <= sentinel_probability <= 1.0:
        raise ValueError("true_sentinel_probability must be in [0, 1]")
    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")

    rng = random.Random(seed)
    target_latent = [
        rng.random() < true_target_probability for _ in range(opportunities)
    ]
    sentinel_latent = [
        rng.random() < sentinel_probability for _ in range(opportunities)
    ]

    target_only = BetaClosurePosterior(1.0, 3.0)
    transfer = BetaClosurePosterior(1.0, 3.0)

    counters = {
        "target_only_credible": {
            "target_exposures": 0,
            "target_failures": 0,
            "false_safe_exposures": 0,
            "first_target_exposure_step": None,
        },
        "shared_sentinel_transfer": {
            "target_exposures": 0,
            "target_failures": 0,
            "false_safe_exposures": 0,
            "first_target_exposure_step": None,
        },
        "oracle_gate": {
            "target_exposures": 0,
            "target_failures": 0,
            "false_safe_exposures": 0,
            "first_target_exposure_step": None,
        },
    }
    truly_safe = _target_is_truly_safe(
        true_target_probability,
        minimum_return_probability,
    )

    for step, (target_closed, sentinel_closed) in enumerate(
        zip(target_latent, sentinel_latent, strict=True),
        start=1,
    ):
        target_allowed = credible_safe_probe_allowed(
            target_only,
            minimum_return_probability=minimum_return_probability,
            confidence=confidence,
        )
        if target_allowed:
            item = counters["target_only_credible"]
            item["target_exposures"] += 1
            item["target_failures"] += int(target_closed)
            item["false_safe_exposures"] += int(not truly_safe)
            if item["first_target_exposure_step"] is None:
                item["first_target_exposure_step"] = step
        target_only = target_only.update(
            exposed=target_allowed,
            closure_observed=target_closed if target_allowed else False,
        )

        transfer = transfer.update(
            exposed=True,
            closure_observed=sentinel_closed,
        )
        transfer_allowed = credible_safe_probe_allowed(
            transfer,
            minimum_return_probability=minimum_return_probability,
            confidence=confidence,
        )
        if transfer_allowed:
            item = counters["shared_sentinel_transfer"]
            item["target_exposures"] += 1
            item["target_failures"] += int(target_closed)
            item["false_safe_exposures"] += int(not truly_safe)
            if item["first_target_exposure_step"] is None:
                item["first_target_exposure_step"] = step

        if truly_safe:
            item = counters["oracle_gate"]
            item["target_exposures"] += 1
            item["target_failures"] += int(target_closed)
            if item["first_target_exposure_step"] is None:
                item["first_target_exposure_step"] = step

    records: list[SideInformationLearningRecord] = []
    for name in (
        "target_only_credible",
        "shared_sentinel_transfer",
        "oracle_gate",
    ):
        if name == "target_only_credible":
            posterior_mean = target_only.mean
            sentinel_observations = 0
        elif name == "shared_sentinel_transfer":
            posterior_mean = transfer.mean
            sentinel_observations = opportunities
        else:
            posterior_mean = true_target_probability
            sentinel_observations = 0
        item = counters[name]
        records.append(
            SideInformationLearningRecord(
                policy=name,
                true_target_probability=true_target_probability,
                true_sentinel_probability=sentinel_probability,
                minimum_return_probability=minimum_return_probability,
                confidence=confidence,
                opportunities=opportunities,
                sentinel_observations=sentinel_observations,
                target_exposures=int(item["target_exposures"]),
                target_failures=int(item["target_failures"]),
                false_safe_exposures=int(item["false_safe_exposures"]),
                posterior_mean=posterior_mean,
                absolute_error=abs(
                    posterior_mean - true_target_probability
                ),
                first_target_exposure_step=(
                    None
                    if item["first_target_exposure_step"] is None
                    else int(item["first_target_exposure_step"])
                ),
            )
        )
    return records
