"""Closed-form two-hazard topology/dependence identities.

These identities make explicit that changing dependence at fixed marginals can
have opposite effects on safe-return reliability depending on topology.

Let C1 and C2 denote closure events with marginal probabilities p1 and p2 and
joint probability q = P(C1 and C2).

* Parallel-redundant return succeeds unless both hazards close:
    R_parallel = 1 - q.
* Serial return succeeds only if neither hazard closes:
    R_serial = 1 - p1 - p2 + q.

Therefore increasing positive dependence (larger q at fixed marginals) lowers
parallel redundancy but raises serial all-open reliability.  This is a topology
interaction, not a universal statement that correlation is harmful or helpful.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TwoHazardDependencePoint:
    p_first: float
    p_second: float
    joint_closure: float

    def validate(self) -> None:
        for name, value in (
            ("p_first", self.p_first),
            ("p_second", self.p_second),
            ("joint_closure", self.joint_closure),
        ):
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        lower = max(0.0, self.p_first + self.p_second - 1.0)
        upper = min(self.p_first, self.p_second)
        if not lower <= self.joint_closure <= upper:
            raise ValueError(
                "joint_closure violates Frechet bounds: "
                f"expected [{lower}, {upper}], got {self.joint_closure}"
            )

    @property
    def independent_joint(self) -> float:
        return self.p_first * self.p_second

    @property
    def dependence_shift(self) -> float:
        """Joint-closure shift relative to independence."""

        return self.joint_closure - self.independent_joint


def parallel_return_probability(point: TwoHazardDependencePoint) -> float:
    """Return reliability for two redundant parallel cut hazards."""

    point.validate()
    return 1.0 - point.joint_closure


def serial_return_probability(point: TwoHazardDependencePoint) -> float:
    """Return reliability when both serial hazard cells must remain open."""

    point.validate()
    return 1.0 - point.p_first - point.p_second + point.joint_closure


def dependence_effect_relative_to_independence(
    point: TwoHazardDependencePoint,
) -> tuple[float, float]:
    """Return (parallel_delta, serial_delta) versus independent dependence.

    Positive dependence shift has equal-magnitude opposite-sign effects:
    parallel_delta = -shift and serial_delta = +shift.
    """

    point.validate()
    shift = point.dependence_shift
    return -shift, shift
