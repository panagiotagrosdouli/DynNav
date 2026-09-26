"""Policy-dependent online calibration benchmark."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass

from dynnav.online_hazard_learning import (
    BetaClosurePosterior,
    SafeProbeCandidate,
    select_safe_information_probe,
)


@dataclass(frozen=True)
class OnlineCalibrationRecord:
    policy: str
    opportunities: int
    exposures: int
    closures: int
    posterior_mean: float
    absolute_error: float
    return_failures: int
    cumulative_exposure_cost: float


def run_online_calibration_benchmark(
    *,
    opportunities: int = 2_000,
    true_closure_probability: float = 0.7,
    minimum_return_probability: float = 0.5,
    seed: int = 0,
) -> list[OnlineCalibrationRecord]:
    """Compare avoidance, unconstrained probing, safe probing and an oracle."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")
    if not 0.0 <= true_closure_probability <= 1.0:
        raise ValueError("true_closure_probability must be in [0, 1]")
    if not 0.0 <= minimum_return_probability <= 1.0:
        raise ValueError("minimum_return_probability must be in [0, 1]")

    rng = random.Random(seed)
    latent = [
        rng.random() < true_closure_probability
        for _ in range(opportunities)
    ]
    policies = {
        "always_avoid": BetaClosurePosterior(1.0, 3.0),
        "always_probe": BetaClosurePosterior(1.0, 3.0),
        "safe_probe": BetaClosurePosterior(1.0, 3.0),
        "oracle_known_probability": BetaClosurePosterior(1.0, 3.0),
    }
    failures = {name: 0 for name in policies}
    costs = {name: 0.0 for name in policies}

    for closure in latent:
        policies["always_avoid"] = policies["always_avoid"].update(exposed=False)

        policies["always_probe"] = policies["always_probe"].update(
            exposed=True,
            closure_observed=closure,
        )
        failures["always_probe"] += int(closure)
        costs["always_probe"] += 1.0

        safe_posterior = policies["safe_probe"]
        predicted_return = 1.0 - safe_posterior.mean
        decision = select_safe_information_probe(
            {0: safe_posterior},
            (
                SafeProbeCandidate(
                    0,
                    predicted_return_probability=predicted_return,
                    traversal_cost=1.0,
                ),
            ),
            minimum_return_probability=minimum_return_probability,
        )
        safe_exposed = decision.hazard_index is not None
        policies["safe_probe"] = safe_posterior.update(
            exposed=safe_exposed,
            closure_observed=closure if safe_exposed else False,
        )
        failures["safe_probe"] += int(safe_exposed and closure)
        costs["safe_probe"] += float(safe_exposed)

        oracle_exposed = (
            1.0 - true_closure_probability >= minimum_return_probability
        )
        policies["oracle_known_probability"] = policies[
            "oracle_known_probability"
        ].update(
            exposed=oracle_exposed,
            closure_observed=closure if oracle_exposed else False,
        )
        failures["oracle_known_probability"] += int(oracle_exposed and closure)
        costs["oracle_known_probability"] += float(oracle_exposed)

    records: list[OnlineCalibrationRecord] = []
    for name, posterior in policies.items():
        estimate = (
            true_closure_probability
            if name == "oracle_known_probability"
            else posterior.mean
        )
        records.append(
            OnlineCalibrationRecord(
                policy=name,
                opportunities=opportunities,
                exposures=posterior.exposures,
                closures=posterior.closures,
                posterior_mean=estimate,
                absolute_error=abs(estimate - true_closure_probability),
                return_failures=failures[name],
                cumulative_exposure_cost=costs[name],
            )
        )
    return records


def records_as_dicts(
    records: list[OnlineCalibrationRecord],
) -> list[dict[str, object]]:
    return [asdict(record) for record in records]
