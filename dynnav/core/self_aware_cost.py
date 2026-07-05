"""Self-aware path cost for uncertainty-aware active navigation."""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.core.navigation_state import PathEvaluation


@dataclass(frozen=True)
class SelfAwareCostWeights:
    """Weights for the self-aware navigation objective.

    The objective is:

        J = alpha * L
          + beta  * R_expected
          + gamma * R_cvar
          + delta * U_localization
          + eta   * U_map
          + zeta  * irreversibility
          - kappa * information_gain

    where irreversibility is represented as 1 - recoverability.
    """

    alpha_length: float = 1.0
    beta_expected_risk: float = 5.0
    gamma_cvar_risk: float = 3.0
    delta_localization_uncertainty: float = 2.0
    eta_map_uncertainty: float = 2.0
    zeta_irreversibility: float = 2.0
    kappa_information_gain: float = 1.5

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value!r}")


def self_aware_path_cost(
    evaluation: PathEvaluation,
    weights: SelfAwareCostWeights | None = None,
) -> float:
    """Return the scalar cost for a candidate path.

    Lower values are better. The function rewards information gain and
    penalizes distance, risk, uncertainty, and irreversibility.
    """
    evaluation.validate()
    weights = weights or SelfAwareCostWeights()
    weights.validate()

    irreversibility = 1.0 - evaluation.recoverability
    return (
        weights.alpha_length * evaluation.path_length
        + weights.beta_expected_risk * evaluation.expected_collision_risk
        + weights.gamma_cvar_risk * evaluation.cvar_tail_risk
        + weights.delta_localization_uncertainty * evaluation.localization_uncertainty
        + weights.eta_map_uncertainty * evaluation.map_uncertainty
        + weights.zeta_irreversibility * irreversibility
        - weights.kappa_information_gain * evaluation.information_gain
    )
