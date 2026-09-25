"""Objective-preservation witness for exact history quotienting.

G5 compresses activated trigger identities when they induce the same future
closure event: identical closure cell and identical closure probability.

For any executed path and initial raw activated-hazard set, this module evaluates
that path in both representations. At every step it checks:

1. the raw active trigger set maps to the quotient active event set;
2. the raw and quotient future-closure distributions induce the same exact
   safe-return probability;
3. therefore the recoverability-augmented transition cost is identical.

Consequently every concrete path has exactly the same cumulative objective
before and after quotienting. The quotient changes the number of search states,
not the objective assigned to a path.
"""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.history_compression import (
    HazardEventQuotient,
    build_hazard_event_quotient,
    quotient_return_probability,
)
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import (
    TopologyHazardBelief,
    exact_safe_return_probability,
)


@dataclass(frozen=True)
class QuotientObjectiveStep:
    cell: GridCell
    raw_active: frozenset[int]
    quotient_active: frozenset[int]
    raw_return_probability: float
    quotient_return_probability: float
    raw_transition_cost: float
    quotient_transition_cost: float


@dataclass(frozen=True)
class QuotientObjectiveWitness:
    steps: tuple[QuotientObjectiveStep, ...]
    raw_total_cost: float
    quotient_total_cost: float
    objective_preserved: bool
    return_profile_preserved: bool


def _raw_hazard_belief(
    model: CommitmentHazardModel,
    active: frozenset[int],
    *,
    current: GridCell,
) -> TopologyHazardBelief:
    probabilities: dict[GridCell, float] = {}
    for index in active:
        if index < 0 or index >= len(model.closures):
            raise ValueError(f"active hazard index out of range: {index}")
        closure = model.closures[index]
        if closure.closure_cell == current:
            continue
        existing = probabilities.get(closure.closure_cell)
        if existing is not None and existing != closure.closure_probability:
            raise ValueError(
                "raw active hazards assign conflicting probabilities "
                f"to {closure.closure_cell}"
            )
        probabilities[closure.closure_cell] = closure.closure_probability
    return TopologyHazardBelief(probabilities)


def _activate_after_transition(
    model: CommitmentHazardModel,
    current: GridCell,
    neighbor: GridCell,
    active: frozenset[int],
) -> frozenset[int]:
    additions = {
        index
        for index, closure in enumerate(model.closures)
        if closure.trigger == (current, neighbor)
    }
    return active | frozenset(additions)


def quotient_path_objective_witness(
    grid: GridMap,
    path: tuple[GridCell, ...] | list[GridCell],
    *,
    safe_cells: set[GridCell],
    hazard_model: CommitmentHazardModel,
    initial_activated_closures: frozenset[int] | None = None,
    step_cost: float = 1.0,
    recoverability_weight: float = 4.0,
    max_hazard_cells: int = 16,
    tolerance: float = 1.0e-12,
) -> QuotientObjectiveWitness:
    """Verify pathwise equality of raw and quotient planning objectives."""

    grid.validate()
    hazard_model.validate(grid)
    if step_cost <= 0.0:
        raise ValueError("step_cost must be positive")
    if recoverability_weight < 0.0:
        raise ValueError("recoverability_weight must be non-negative")
    if max_hazard_cells < 0:
        raise ValueError("max_hazard_cells must be non-negative")
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")

    cells = tuple(path)
    if not cells:
        raise ValueError("path cannot be empty")
    for cell in cells:
        if not grid.in_bounds(cell) or not grid.passable(cell):
            raise ValueError(f"path contains invalid cell: {cell}")
    for first, second in zip(cells, cells[1:], strict=False):
        if second not in grid.neighbors4(first):
            raise ValueError(f"path has non-adjacent transition: {first}->{second}")

    quotient: HazardEventQuotient = build_hazard_event_quotient(hazard_model)
    raw_active = frozenset(initial_activated_closures or ())
    quotient_active = quotient.compress_active_indices(raw_active)

    steps: list[QuotientObjectiveStep] = []
    raw_total = 0.0
    quotient_total = 0.0

    for current, neighbor in zip(cells, cells[1:], strict=False):
        raw_active = _activate_after_transition(
            hazard_model,
            current,
            neighbor,
            raw_active,
        )
        quotient_active = quotient.compress_active_indices(raw_active)

        raw_probability = exact_safe_return_probability(
            grid,
            neighbor,
            safe_cells,
            _raw_hazard_belief(
                hazard_model,
                raw_active,
                current=neighbor,
            ),
            max_hazard_cells=max_hazard_cells,
        )
        compressed_probability = quotient_return_probability(
            grid,
            neighbor,
            safe_cells,
            quotient,
            quotient_active,
            max_hazard_cells=max_hazard_cells,
        )
        raw_transition = step_cost + recoverability_weight * (
            1.0 - raw_probability
        )
        quotient_transition = step_cost + recoverability_weight * (
            1.0 - compressed_probability
        )
        raw_total += raw_transition
        quotient_total += quotient_transition
        steps.append(
            QuotientObjectiveStep(
                cell=neighbor,
                raw_active=raw_active,
                quotient_active=quotient_active,
                raw_return_probability=raw_probability,
                quotient_return_probability=compressed_probability,
                raw_transition_cost=raw_transition,
                quotient_transition_cost=quotient_transition,
            )
        )

    return_profile_preserved = all(
        abs(step.raw_return_probability - step.quotient_return_probability)
        <= tolerance
        for step in steps
    )
    objective_preserved = (
        return_profile_preserved
        and abs(raw_total - quotient_total) <= tolerance
        and all(
            abs(step.raw_transition_cost - step.quotient_transition_cost)
            <= tolerance
            for step in steps
        )
    )
    return QuotientObjectiveWitness(
        steps=tuple(steps),
        raw_total_cost=raw_total,
        quotient_total_cost=quotient_total,
        objective_preserved=objective_preserved,
        return_profile_preserved=return_profile_preserved,
    )
