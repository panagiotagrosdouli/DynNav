"""Runtime semantics for paired two-hazard dependence experiments."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from dynnav_nav2_benchmark.history_execution import (
    classify_observed_cells,
    transition_text,
)

GridCell = tuple[int, int]
DirectedTransition = tuple[GridCell, GridCell]


@dataclass(frozen=True)
class CorrelatedHazardRuntimeSpec:
    hazard_id: str
    trigger: DirectedTransition
    closure_probability: float

    def __post_init__(self) -> None:
        if not self.hazard_id:
            raise ValueError("hazard_id cannot be empty")
        if not 0.0 <= self.closure_probability <= 1.0:
            raise ValueError("closure_probability must be in [0, 1]")


def _stable_draw(*parts: object) -> float:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).digest()
    seed = int.from_bytes(digest[:8], "big")
    return random.Random(seed).random()


def paired_closure_outcomes(
    *,
    seed: int,
    scenario_name: str,
    repetition: int,
    dependence: str,
    closure_probability: float = 0.5,
) -> tuple[bool, bool]:
    """Return planner-independent paired latent outcomes with fixed marginals.

    The anti-correlated construction is currently restricted to p=0.5 because
    exactly-one-closure then preserves both marginals without additional mass.
    """

    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")
    if dependence == "independent":
        return (
            _stable_draw(seed, scenario_name, repetition, "hazard_0")
            < closure_probability,
            _stable_draw(seed, scenario_name, repetition, "hazard_1")
            < closure_probability,
        )
    shared = _stable_draw(seed, scenario_name, repetition, "shared_dependence")
    if dependence == "common_cause":
        event = shared < closure_probability
        return event, event
    if dependence == "anti_correlated":
        if abs(closure_probability - 0.5) > 1.0e-12:
            raise ValueError("anti_correlated exact-marginal construction requires p=0.5")
        first = shared < 0.5
        return first, not first
    raise ValueError(f"unknown dependence condition: {dependence}")


@dataclass(slots=True)
class CorrelatedHistoryRuntimeState:
    hazards: tuple[CorrelatedHazardRuntimeSpec, CorrelatedHazardRuntimeSpec]
    latent_closures: tuple[bool, bool]
    previous_cell: GridCell | None = None
    accepted_transitions: list[str] = field(default_factory=list)
    sampling_gaps: list[tuple[GridCell, GridCell]] = field(default_factory=list)
    trigger_observed: list[bool] = field(default_factory=lambda: [False, False])
    closure_requested: list[bool] = field(default_factory=lambda: [False, False])

    def __post_init__(self) -> None:
        if len(self.hazards) != 2 or len(self.latent_closures) != 2:
            raise ValueError("correlated runtime requires exactly two hazards")

    def observe(self, cell: GridCell) -> str | None:
        if self.previous_cell is None:
            self.previous_cell = cell
            return None
        observed = classify_observed_cells(self.previous_cell, cell)
        self.previous_cell = cell
        if observed.kind == "sampling_gap":
            self.sampling_gaps.append((observed.source, observed.target))
            return None
        if observed.transition is None:
            return None

        text = transition_text(observed.transition)
        self.accepted_transitions.append(text)
        for index, hazard in enumerate(self.hazards):
            if observed.transition == hazard.trigger:
                self.trigger_observed[index] = True
                self.closure_requested[index] = self.latent_closures[index]
        return text

    @property
    def observation_valid(self) -> bool:
        return not self.sampling_gaps

    @property
    def activated_count(self) -> int:
        return sum(self.trigger_observed)

    @property
    def requested_closure_count(self) -> int:
        return sum(self.closure_requested)

    def hazard_outcomes(self) -> list[dict[str, object]]:
        return [
            {
                "hazard_id": hazard.hazard_id,
                "trigger_observed": self.trigger_observed[index],
                "closure_realized": self.latent_closures[index],
                "closure_requested": self.closure_requested[index],
            }
            for index, hazard in enumerate(self.hazards)
        ]
