"""Team coordination metrics for Contribution 09.

Contribution 09 studies decentralized multi-robot coordination. This module makes
coordination quality measurable by checking:

- spatial-temporal path conflicts,
- risk budget allocation,
- team-level feasibility,
- disagreement between robot belief summaries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from numbers import Integral
from typing import Iterable

Node = tuple[int, int]
TimedPath = list[Node]


@dataclass(frozen=True)
class RobotPlan:
    robot_id: str
    path: TimedPath
    risk: float
    allocated_risk_budget: float
    belief_hash: str = ""

    def __post_init__(self) -> None:
        if not self.robot_id:
            raise ValueError("robot_id must not be empty")
        if not self.path:
            raise ValueError("robot path must not be empty")
        if any(not isinstance(node, (tuple, list)) or len(node) != 2
               or any(not isinstance(v, Integral) for v in node) for node in self.path):
            raise ValueError("path nodes must be integer (row, column) pairs")
        if not math.isfinite(self.risk) or not 0 <= self.risk <= 1:
            raise ValueError("risk must be finite and in [0, 1]")
        if not math.isfinite(self.allocated_risk_budget) or not 0 <= self.allocated_risk_budget <= 1:
            raise ValueError("allocated_risk_budget must be finite and in [0, 1]")


@dataclass(frozen=True)
class ConflictEvent:
    t: int
    robot_a: str
    robot_b: str
    conflict_type: str
    location: str

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass(frozen=True)
class TeamCoordinationReport:
    n_robots: int
    n_conflicts: int
    vertex_conflicts: int
    edge_swap_conflicts: int
    total_risk: float
    total_budget: float
    risk_budget_violations: int
    belief_disagreement_count: int
    feasible: bool

    def to_dict(self) -> dict[str, float | int | bool]:
        return asdict(self)


def _position_at(path: TimedPath, t: int) -> Node:
    if not path:
        raise ValueError("Robot path must not be empty.")
    return path[min(t, len(path) - 1)]


def detect_path_conflicts(plans: Iterable[RobotPlan]) -> list[ConflictEvent]:
    plans = list(plans)
    if not plans:
        return []
    _validate_unique_robot_ids(plans)
    horizon = max(len(p.path) for p in plans)
    events: list[ConflictEvent] = []

    for t in range(horizon):
        for i in range(len(plans)):
            for j in range(i + 1, len(plans)):
                a = plans[i]
                b = plans[j]
                a_now = _position_at(a.path, t)
                b_now = _position_at(b.path, t)
                if a_now == b_now:
                    events.append(ConflictEvent(t, a.robot_id, b.robot_id, "vertex", str(a_now)))

                if t > 0:
                    a_prev = _position_at(a.path, t - 1)
                    b_prev = _position_at(b.path, t - 1)
                    if a_prev == b_now and b_prev == a_now and a_now != b_now:
                        events.append(ConflictEvent(t, a.robot_id, b.robot_id, "edge_swap", f"{a_prev}<->{a_now}"))
    return events


def count_belief_disagreements(plans: Iterable[RobotPlan]) -> int:
    plans = list(plans)
    _validate_unique_robot_ids(plans)
    hashes = [p.belief_hash for p in plans if p.belief_hash]
    if not hashes:
        return 0
    majority = max(set(hashes), key=hashes.count)
    return sum(h != majority for h in hashes)


def summarize_team_coordination(plans: Iterable[RobotPlan]) -> TeamCoordinationReport:
    plans = list(plans)
    _validate_unique_robot_ids(plans)
    conflicts = detect_path_conflicts(plans)
    vertex = sum(c.conflict_type == "vertex" for c in conflicts)
    edge = sum(c.conflict_type == "edge_swap" for c in conflicts)
    total_risk = sum(float(p.risk) for p in plans)
    total_budget = sum(float(p.allocated_risk_budget) for p in plans)
    risk_violations = sum(float(p.risk) > float(p.allocated_risk_budget) for p in plans)
    disagreements = count_belief_disagreements(plans)
    feasible = len(conflicts) == 0 and risk_violations == 0 and disagreements == 0

    return TeamCoordinationReport(
        n_robots=len(plans),
        n_conflicts=len(conflicts),
        vertex_conflicts=vertex,
        edge_swap_conflicts=edge,
        total_risk=float(total_risk),
        total_budget=float(total_budget),
        risk_budget_violations=int(risk_violations),
        belief_disagreement_count=int(disagreements),
        feasible=bool(feasible),
    )


def _validate_unique_robot_ids(plans: list[RobotPlan]) -> None:
    ids = [plan.robot_id for plan in plans]
    if len(set(ids)) != len(ids):
        raise ValueError("robot_id values must be unique within a team")
