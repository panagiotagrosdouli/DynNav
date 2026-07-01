"""Resource feasibility utilities for Contribution 06.

Contribution 06 studies navigation under resource constraints. This module makes
those constraints explicit and auditable by evaluating candidate missions using:

- energy budget margin,
- minimum connectivity margin,
- recharge/relay recommendations,
- mission verdicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable


class MissionVerdict(str, Enum):
    DIRECT_FEASIBLE = "DIRECT_FEASIBLE"
    NEEDS_RECHARGE = "NEEDS_RECHARGE"
    NEEDS_RELAY = "NEEDS_RELAY"
    NEEDS_RECHARGE_AND_RELAY = "NEEDS_RECHARGE_AND_RELAY"
    INFEASIBLE = "INFEASIBLE"


@dataclass(frozen=True)
class ResourceConfig:
    battery_budget: float
    reserve_energy: float = 2.0
    min_connectivity: float = 0.35
    energy_per_meter: float = 1.0

    def usable_energy(self) -> float:
        return max(0.0, self.battery_budget - self.reserve_energy)


@dataclass(frozen=True)
class CandidateRoute:
    name: str
    distance: float
    min_connectivity: float
    mean_connectivity: float
    via_recharge: bool = False
    via_relay: bool = False


@dataclass(frozen=True)
class ResourceReport:
    route_name: str
    verdict: MissionVerdict
    distance: float
    energy_required: float
    usable_energy: float
    energy_margin: float
    min_connectivity: float
    connectivity_margin: float
    via_recharge: bool
    via_relay: bool
    feasible: bool

    def to_dict(self) -> dict[str, float | bool | str]:
        row = asdict(self)
        row["verdict"] = self.verdict.value
        return row


def energy_required(route: CandidateRoute, cfg: ResourceConfig) -> float:
    return float(route.distance * cfg.energy_per_meter)


def classify_route(route: CandidateRoute, cfg: ResourceConfig) -> ResourceReport:
    required = energy_required(route, cfg)
    usable = cfg.usable_energy()
    energy_margin = usable - required
    connectivity_margin = route.min_connectivity - cfg.min_connectivity
    energy_ok = energy_margin >= 0.0 or route.via_recharge
    connectivity_ok = connectivity_margin >= 0.0 or route.via_relay

    if energy_ok and connectivity_ok and not route.via_recharge and not route.via_relay:
        verdict = MissionVerdict.DIRECT_FEASIBLE
    elif energy_ok and connectivity_ok and route.via_recharge and route.via_relay:
        verdict = MissionVerdict.NEEDS_RECHARGE_AND_RELAY
    elif energy_ok and connectivity_ok and route.via_recharge:
        verdict = MissionVerdict.NEEDS_RECHARGE
    elif energy_ok and connectivity_ok and route.via_relay:
        verdict = MissionVerdict.NEEDS_RELAY
    else:
        verdict = MissionVerdict.INFEASIBLE

    return ResourceReport(
        route_name=route.name,
        verdict=verdict,
        distance=float(route.distance),
        energy_required=required,
        usable_energy=usable,
        energy_margin=float(energy_margin),
        min_connectivity=float(route.min_connectivity),
        connectivity_margin=float(connectivity_margin),
        via_recharge=route.via_recharge,
        via_relay=route.via_relay,
        feasible=verdict != MissionVerdict.INFEASIBLE,
    )


def choose_best_feasible(reports: Iterable[ResourceReport]) -> ResourceReport | None:
    feasible = [r for r in reports if r.feasible]
    if not feasible:
        return None
    verdict_rank = {
        MissionVerdict.DIRECT_FEASIBLE: 0,
        MissionVerdict.NEEDS_RELAY: 1,
        MissionVerdict.NEEDS_RECHARGE: 2,
        MissionVerdict.NEEDS_RECHARGE_AND_RELAY: 3,
        MissionVerdict.INFEASIBLE: 99,
    }
    return min(
        feasible,
        key=lambda r: (
            verdict_rank[r.verdict],
            r.distance,
            -r.energy_margin,
            -r.connectivity_margin,
        ),
    )
