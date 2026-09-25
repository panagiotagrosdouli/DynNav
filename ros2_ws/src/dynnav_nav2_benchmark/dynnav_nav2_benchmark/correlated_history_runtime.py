"""Runtime semantics for paired two-hazard dependence experiments."""

from __future__ import annotations

import hashlib
import math
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
    trigger_edges: tuple[DirectedTransition, ...] = ()
    gate_x: float | None = None
    gate_center_y: float | None = None
    gate_half_width_m: float = 0.0
    origin_y: float = 0.0
    resolution: float = 1.0

    def __post_init__(self) -> None:
        if not self.hazard_id:
            raise ValueError("hazard_id cannot be empty")
        if not 0.0 <= self.closure_probability <= 1.0:
            raise ValueError("closure_probability must be in [0, 1]")
        if self.gate_half_width_m < 0.0 or not math.isfinite(self.gate_half_width_m):
            raise ValueError("gate_half_width_m must be finite and non-negative")
        if self.resolution <= 0.0 or not math.isfinite(self.resolution):
            raise ValueError("resolution must be finite and positive")


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
    """Return planner-independent paired latent outcomes with fixed marginals."""

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
    previous_world: tuple[float, float] | None = None
    accepted_transitions: list[str] = field(default_factory=list)
    sampling_gaps: list[tuple[GridCell, GridCell]] = field(default_factory=list)
    localization_jumps: list[tuple[tuple[float, float], tuple[float, float]]] = field(
        default_factory=list
    )
    trigger_observed: list[bool] = field(default_factory=lambda: [False, False])
    closure_requested: list[bool] = field(default_factory=lambda: [False, False])

    def __post_init__(self) -> None:
        if len(self.hazards) != 2 or len(self.latent_closures) != 2:
            raise ValueError("correlated runtime requires exactly two hazards")

    def observe(self, cell: GridCell) -> str | None:
        """Legacy cell-sampled observation retained for unit/regression tests."""

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
            edges = hazard.trigger_edges or (hazard.trigger,)
            if observed.transition in edges:
                self.trigger_observed[index] = True
                self.closure_requested[index] = self.latent_closures[index]
        return text

    def observe_world(
        self,
        x: float,
        y: float,
        *,
        maximum_continuous_step_m: float = 0.75,
    ) -> tuple[str, ...]:
        """Observe continuous robot motion and emit executed gate crossings.

        Normal multi-cell motion between controller feedback samples is valid.
        Only a large discontinuity is treated as a localization jump. Trigger
        crossing is computed geometrically on the line segment between
        successive poses and then mapped to the corresponding predeclared grid
        edge in the trigger gate.
        """

        current = (float(x), float(y))
        if self.previous_world is None:
            self.previous_world = current
            return ()

        previous = self.previous_world
        self.previous_world = current
        if math.hypot(current[0] - previous[0], current[1] - previous[1]) > maximum_continuous_step_m:
            self.localization_jumps.append((previous, current))
            return ()

        emitted: list[str] = []
        for index, hazard in enumerate(self.hazards):
            if self.trigger_observed[index] or hazard.gate_x is None:
                continue
            dx = current[0] - previous[0]
            if abs(dx) <= 1.0e-12:
                continue

            direction = 1 if hazard.trigger[1][0] > hazard.trigger[0][0] else -1
            crossed = (
                previous[0] < hazard.gate_x <= current[0]
                if direction > 0
                else previous[0] > hazard.gate_x >= current[0]
            )
            if not crossed:
                continue

            fraction = (hazard.gate_x - previous[0]) / dx
            y_cross = previous[1] + fraction * (current[1] - previous[1])
            gate_y = (
                hazard.gate_center_y
                if hazard.gate_center_y is not None
                else y_cross
            )
            if abs(y_cross - gate_y) > hazard.gate_half_width_m + 1.0e-12:
                continue

            candidate_edges = hazard.trigger_edges or (hazard.trigger,)
            crossing_y_cell = math.floor(
                (y_cross - hazard.origin_y) / hazard.resolution
            )
            edge = min(
                candidate_edges,
                key=lambda item: abs(item[0][1] - crossing_y_cell),
            )
            text = transition_text(edge)
            emitted.append(text)
            self.accepted_transitions.append(text)
            self.trigger_observed[index] = True
            self.closure_requested[index] = self.latent_closures[index]

        return tuple(emitted)

    @property
    def observation_valid(self) -> bool:
        return not self.localization_jumps

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
