"""Runtime state for action-triggered history execution trials."""

from dataclasses import dataclass, field

from dynnav_nav2_benchmark.history_execution import (
    classify_observed_cells,
    transition_text,
    trigger_decision,
)


@dataclass(slots=True)
class HistoryRuntimeState:
    trigger: tuple[tuple[int, int], tuple[int, int]]
    latent_draw: float
    closure_probability: float
    previous_cell: tuple[int, int] | None = None
    accepted_transitions: list[str] = field(default_factory=list)
    sampling_gaps: list[tuple[tuple[int, int], tuple[int, int]]] = field(
        default_factory=list
    )
    trigger_observed: bool = False
    closure_requested: bool = False

    @property
    def closure_realized(self) -> bool:
        """Return the frozen latent event outcome for this paired trial."""
        return self.latent_draw < self.closure_probability

    @property
    def event_outcome(self) -> str:
        """Describe the event outcome using the trigger observed so far."""
        if not self.trigger_observed:
            return "trigger_avoided"
        if self.closure_realized:
            return "closure_should_apply"
        return "trigger_observed_no_closure"

    def observe(self, cell: tuple[int, int]) -> str | None:
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
        decision = trigger_decision(
            observed=observed.transition,
            trigger=self.trigger,
            latent_draw=self.latent_draw,
            closure_probability=self.closure_probability,
        )
        if decision.trigger_observed:
            self.trigger_observed = True
            self.closure_requested = decision.event_should_apply
        return text

    @property
    def observation_valid(self) -> bool:
        return not self.sampling_gaps
