"""Multi-sensor trust fusion for the DynNav security research prototype."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import prod
from typing import Mapping

from .events import TrustState


class FusionMethod(str, Enum):
    MINIMUM = "minimum"
    WEIGHTED_MEAN = "weighted_mean"
    RELIABILITY_WEIGHTED = "reliability_weighted"
    BAYESIAN_STYLE = "bayesian_style"
    MAJORITY_CONSISTENCY = "majority_consistency"


@dataclass(frozen=True)
class FusedTrust:
    value: float
    confidence: float
    method: FusionMethod
    contributors: tuple[str, ...]
    diagnostics: dict[str, float]


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def fuse_trust(
    states: Mapping[str, TrustState],
    method: FusionMethod | str = FusionMethod.RELIABILITY_WEIGHTED,
    weights: Mapping[str, float] | None = None,
) -> FusedTrust:
    if not states:
        raise ValueError("at least one trust state is required")
    method = FusionMethod(method)
    names = tuple(sorted(states))
    trust = {name: _clip(states[name].filtered_trust) for name in names}
    confidence = {name: _clip(states[name].confidence) for name in names}
    configured = weights or {}

    if method is FusionMethod.MINIMUM:
        value = min(trust.values())
        fused_confidence = confidence[min(trust, key=trust.get)]
    elif method is FusionMethod.WEIGHTED_MEAN:
        effective = {name: max(0.0, float(configured.get(name, 1.0))) for name in names}
        denominator = sum(effective.values())
        if denominator <= 0.0:
            raise ValueError("fusion weights must contain a positive value")
        value = sum(effective[name] * trust[name] for name in names) / denominator
        fused_confidence = sum(effective[name] * confidence[name] for name in names) / denominator
    elif method is FusionMethod.RELIABILITY_WEIGHTED:
        effective = {
            name: max(0.0, float(configured.get(name, 1.0))) * max(confidence[name], 1e-6)
            for name in names
        }
        denominator = sum(effective.values())
        value = sum(effective[name] * trust[name] for name in names) / denominator
        fused_confidence = sum(effective[name] * confidence[name] for name in names) / denominator
    elif method is FusionMethod.BAYESIAN_STYLE:
        reliable = prod(max(1e-9, trust[name] * confidence[name]) for name in names)
        unreliable = prod(max(1e-9, (1.0 - trust[name]) * confidence[name]) for name in names)
        value = reliable / (reliable + unreliable)
        fused_confidence = 1.0 - prod(1.0 - confidence[name] for name in names)
    else:
        healthy_votes = sum(value >= 0.5 for value in trust.values())
        value = healthy_votes / len(names)
        fused_confidence = sum(confidence.values()) / len(names)

    return FusedTrust(
        value=_clip(value),
        confidence=_clip(fused_confidence),
        method=method,
        contributors=names,
        diagnostics={"minimum": min(trust.values()), "maximum": max(trust.values())},
    )
