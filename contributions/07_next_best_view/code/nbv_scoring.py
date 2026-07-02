"""Next-Best-View scoring utilities for Contribution 07.

Contribution 07 studies active exploration. This module makes the viewpoint
selection objective explicit and extends classic information-gain scoring with
risk and returnability terms.

A good viewpoint should not only reveal many unknown cells. It should also be
reachable, reasonably low-risk, and preserve the robot's ability to recover.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class ViewCandidate:
    name: str
    information_gain: float
    travel_cost: float
    path_risk: float
    returnability: float
    connectivity: float = 1.0


@dataclass(frozen=True)
class NBVScore:
    name: str
    information_gain: float
    travel_cost: float
    path_risk: float
    returnability: float
    connectivity: float
    classic_score: float
    safe_score: float
    selected_by_classic: bool = False
    selected_by_safe: bool = False

    def to_dict(self) -> dict[str, float | bool | str]:
        return asdict(self)


@dataclass(frozen=True)
class NBVWeights:
    risk_weight: float = 1.0
    returnability_weight: float = 1.0
    connectivity_weight: float = 0.25
    epsilon: float = 1e-9


def classic_nbv_score(candidate: ViewCandidate, epsilon: float = 1e-9) -> float:
    """Classic greedy NBV score: information gain divided by travel cost."""
    return float(candidate.information_gain / max(candidate.travel_cost, epsilon))


def safe_nbv_score(candidate: ViewCandidate, weights: NBVWeights | None = None) -> float:
    """Returnability-aware NBV score.

    The score rewards information gain and returnability, while penalizing travel
    cost and path risk. Connectivity is treated as a mild bonus because a view
    that preserves communication is operationally stronger.
    """
    w = weights or NBVWeights()
    denominator = max(candidate.travel_cost, w.epsilon) * (1.0 + w.risk_weight * max(candidate.path_risk, 0.0))
    recovery_bonus = 1.0 + w.returnability_weight * max(0.0, min(1.0, candidate.returnability))
    connectivity_bonus = 1.0 + w.connectivity_weight * max(0.0, min(1.0, candidate.connectivity))
    return float(candidate.information_gain * recovery_bonus * connectivity_bonus / denominator)


def score_candidates(candidates: Iterable[ViewCandidate], weights: NBVWeights | None = None) -> list[NBVScore]:
    candidates = list(candidates)
    if not candidates:
        raise ValueError("At least one candidate viewpoint is required.")
    w = weights or NBVWeights()
    classic_values = [classic_nbv_score(c, epsilon=w.epsilon) for c in candidates]
    safe_values = [safe_nbv_score(c, weights=w) for c in candidates]
    classic_best = max(range(len(candidates)), key=lambda i: classic_values[i])
    safe_best = max(range(len(candidates)), key=lambda i: safe_values[i])

    rows: list[NBVScore] = []
    for i, c in enumerate(candidates):
        rows.append(
            NBVScore(
                name=c.name,
                information_gain=float(c.information_gain),
                travel_cost=float(c.travel_cost),
                path_risk=float(c.path_risk),
                returnability=float(c.returnability),
                connectivity=float(c.connectivity),
                classic_score=float(classic_values[i]),
                safe_score=float(safe_values[i]),
                selected_by_classic=i == classic_best,
                selected_by_safe=i == safe_best,
            )
        )
    return rows
