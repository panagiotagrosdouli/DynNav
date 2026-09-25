"""Exact event-state compression for commitment hazards.

Multiple directed triggers may activate the same future closure event.  Tracking
their trigger identities separately creates redundant augmented states.  This
module constructs an exact quotient by closure-event semantics: hazards are
equivalent when they close the same cell with the same probability.

The quotient preserves the independent-closure distribution used by DynNav.
It is intentionally conservative; it does not merge distinct closure events
merely because they happen to have equal recoverability in one map.
"""

from __future__ import annotations

from dataclasses import dataclass

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability

HazardEventKey = tuple[GridCell, float]


@dataclass(frozen=True)
class HazardEventQuotient:
    event_keys: tuple[HazardEventKey, ...]
    event_by_hazard_index: tuple[int, ...]

    @property
    def hazard_count(self) -> int:
        return len(self.event_by_hazard_index)

    @property
    def event_count(self) -> int:
        return len(self.event_keys)

    @property
    def worst_case_state_count_reduction(self) -> int:
        return (2 ** self.hazard_count) - (2 ** self.event_count)

    def compress_active_indices(self, active: frozenset[int]) -> frozenset[int]:
        invalid = sorted(index for index in active if index < 0 or index >= self.hazard_count)
        if invalid:
            raise ValueError(f"active hazard indices out of range: {invalid}")
        return frozenset(self.event_by_hazard_index[index] for index in active)

    def hazard_belief_from_events(
        self,
        active_events: frozenset[int],
        *,
        current: GridCell | None = None,
    ) -> TopologyHazardBelief:
        invalid = sorted(index for index in active_events if index < 0 or index >= self.event_count)
        if invalid:
            raise ValueError(f"active event indices out of range: {invalid}")
        probabilities = {
            cell: probability
            for index, (cell, probability) in enumerate(self.event_keys)
            if index in active_events and cell != current
        }
        return TopologyHazardBelief(probabilities)


def build_hazard_event_quotient(model: CommitmentHazardModel) -> HazardEventQuotient:
    key_to_event: dict[HazardEventKey, int] = {}
    event_keys: list[HazardEventKey] = []
    event_by_hazard: list[int] = []
    for closure in model.closures:
        key = (closure.closure_cell, float(closure.closure_probability))
        event_index = key_to_event.get(key)
        if event_index is None:
            event_index = len(event_keys)
            key_to_event[key] = event_index
            event_keys.append(key)
        event_by_hazard.append(event_index)
    return HazardEventQuotient(tuple(event_keys), tuple(event_by_hazard))


def quotient_return_probability(
    grid: GridMap,
    current: GridCell,
    safe_cells: set[GridCell],
    quotient: HazardEventQuotient,
    active_events: frozenset[int],
    *,
    max_hazard_cells: int = 16,
) -> float:
    """Evaluate safe return directly from the compressed event state."""

    hazard = quotient.hazard_belief_from_events(active_events, current=current)
    return exact_safe_return_probability(
        grid,
        current,
        safe_cells,
        hazard,
        max_hazard_cells=max_hazard_cells,
    )
