"""Receding-horizon V4 execution under latent hazard arming and noisy observations.

The simulator keeps ground truth separate from planner information. Random
events use keyed SHA-256 uniforms so route divergence or planner ordering does
not shift the event assigned to a hazard.

This module provides the execution semantics required by EXPERIMENT_PROTOCOL_V4.
It does not itself define the frozen held-out scenario manifest.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum

from dynnav.activation_belief import ActivationBelief, expected_safe_return_probability
from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.belief_commitment_astar import (
    BeliefCommitmentAStarConfig,
    belief_commitment_astar,
)
from dynnav.planners.commitment_aware_astar import (
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.recoverability_belief import TopologyHazardBelief, exact_safe_return_probability
from dynnav.recoverability_scenarios import (
    ClosureScenario,
    TopologyScenarioBelief,
    exact_scenario_safe_return_probability,
)


class V4Planner(str, Enum):
    SHORTEST = "shortest"
    FIXED_MARGINAL_EXACT = "fixed_marginal_exact"
    ACTIVATION_ORACLE = "activation_oracle"
    DETECTOR_AS_TRUTH = "detector_as_truth"
    BELIEF = "belief"
    HARD_BELIEF = "hard_belief"
    PRIOR_ONLY = "prior_only"


@dataclass(frozen=True)
class V4ExecutionScenario:
    name: str
    grid: GridMap
    start: GridCell
    goal: GridCell
    safe_cells: frozenset[GridCell]
    hazard_model: CommitmentHazardModel
    arming_probabilities: tuple[float, ...]
    detection_sensitivities: tuple[float, ...]
    detection_specificities: tuple[float, ...]
    recoverability_weight: float = 8.0
    hard_return_threshold: float = 0.9
    assumed_arming_probabilities: tuple[float, ...] | None = None
    assumed_detection_sensitivities: tuple[float, ...] | None = None
    assumed_detection_specificities: tuple[float, ...] | None = None

    def planning_arming_probabilities(self) -> tuple[float, ...]:
        return (
            self.arming_probabilities
            if self.assumed_arming_probabilities is None
            else self.assumed_arming_probabilities
        )

    def planning_detection_sensitivities(self) -> tuple[float, ...]:
        return (
            self.detection_sensitivities
            if self.assumed_detection_sensitivities is None
            else self.assumed_detection_sensitivities
        )

    def planning_detection_specificities(self) -> tuple[float, ...]:
        return (
            self.detection_specificities
            if self.assumed_detection_specificities is None
            else self.assumed_detection_specificities
        )

    def validate(self) -> None:
        self.grid.validate()
        self.hazard_model.validate(self.grid)
        n = len(self.hazard_model.closures)
        for label, values in (
            ("arming_probabilities", self.arming_probabilities),
            ("detection_sensitivities", self.detection_sensitivities),
            ("detection_specificities", self.detection_specificities),
            ("planning_arming_probabilities", self.planning_arming_probabilities()),
            (
                "planning_detection_sensitivities",
                self.planning_detection_sensitivities(),
            ),
            (
                "planning_detection_specificities",
                self.planning_detection_specificities(),
            ),
        ):
            if len(values) != n:
                raise ValueError(f"{label} must have one value per hazard")
            if any(not 0.0 <= float(value) <= 1.0 for value in values):
                raise ValueError(f"{label} values must be in [0, 1]")
        if not self.safe_cells:
            raise ValueError("safe_cells cannot be empty")
        if not self.grid.in_bounds(self.start) or not self.grid.passable(self.start):
            raise ValueError("start must be a free grid cell")
        if not self.grid.in_bounds(self.goal) or not self.grid.passable(self.goal):
            raise ValueError("goal must be a free grid cell")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")
        if not 0.0 <= self.hard_return_threshold <= 1.0:
            raise ValueError("hard_return_threshold must be in [0, 1]")


@dataclass(frozen=True)
class V4ExecutionRecord:
    scenario: str
    seed: int
    planner: str
    mission_success: bool
    path: tuple[GridCell, ...]
    path_length: int
    true_armed_set: tuple[int, ...]
    estimated_armed_set: tuple[int, ...]
    trigger_ids_executed: tuple[int, ...]
    detector_observations: tuple[tuple[int, int, bool], ...]
    observation_count: int
    final_belief_support_size: int
    final_belief_entropy_bits: float
    final_true_armed_posterior_probability: float
    predicted_return_probability: float
    true_model_return_probability: float
    realized_closure_cells: tuple[GridCell, ...]
    return_feasible: bool
    planning_calls: int
    nodes_expanded: int
    planning_time_ms: float
    protocol_valid: bool
    invalid_reason: str


def keyed_uniform(
    scenario: str,
    seed: int,
    hazard_index: int,
    event_type: str,
    occurrence_index: int = 0,
) -> float:
    """Return a deterministic uniform draw keyed independently of call order."""

    payload = (
        f"{scenario}|{seed}|{hazard_index}|{event_type}|{occurrence_index}"
    ).encode()
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


def _fixed_marginal_hazard(scenario: V4ExecutionScenario) -> TopologyHazardBelief:
    probabilities: dict[GridCell, float] = {}
    for index, closure in enumerate(scenario.hazard_model.closures):
        marginal = (
            scenario.arming_probabilities[index] * closure.closure_probability
        )
        existing = probabilities.get(closure.closure_cell)
        if existing is not None and not math.isclose(existing, marginal, abs_tol=1e-12):
            raise ValueError(
                "fixed-marginal baseline requires one marginal per closure cell"
            )
        probabilities[closure.closure_cell] = marginal
    return TopologyHazardBelief(probabilities)


def _point_belief(active: set[int]) -> ActivationBelief:
    return ActivationBelief.certain_active(active)


def update_latched_detector_estimate(
    detector_active: set[int],
    hazard_index: int,
    *,
    observed_armed: bool,
) -> None:
    """Update the frozen P3 positive-latching point estimate.

    The V4 latent arming state is monotone. P3 deliberately collapses noisy
    observations to a persistent binary estimate: a positive observation
    latches the hazard as armed, while later negative observations cannot clear
    it. This is a naive comparator, not a Bayesian update.
    """
    if hazard_index < 0:
        raise ValueError("hazard_index must be non-negative")
    if observed_armed:
        detector_active.add(hazard_index)


def _plan_next(
    scenario: V4ExecutionScenario,
    planner: V4Planner,
    current: GridCell,
    *,
    true_active: set[int],
    detector_active: set[int],
    belief: ActivationBelief,
    prior_only_belief: ActivationBelief,
):
    safe = set(scenario.safe_cells)
    if planner is V4Planner.SHORTEST:
        return commitment_aware_astar(
            scenario.grid,
            current,
            scenario.goal,
            safe_cells=safe,
            hazard_model=scenario.hazard_model,
            mode=CommitmentPlannerMode.SHORTEST,
        )

    if planner is V4Planner.FIXED_MARGINAL_EXACT:
        return hazard_reliability_astar(
            scenario.grid,
            current,
            scenario.goal,
            safe_cells=safe,
            hazard=_fixed_marginal_hazard(scenario),
            mode=HazardReliabilityMode.EXACT_RETURN,
            config=HazardReliabilityAStarConfig(
                reliability_weight=scenario.recoverability_weight,
                max_hazard_cells=max(16, len(scenario.hazard_model.closures)),
            ),
        )

    if planner is V4Planner.ACTIVATION_ORACLE:
        current_belief = _point_belief(true_active)
        threshold = None
    elif planner is V4Planner.DETECTOR_AS_TRUTH:
        current_belief = _point_belief(detector_active)
        threshold = None
    elif planner is V4Planner.PRIOR_ONLY:
        current_belief = prior_only_belief
        threshold = None
    else:
        current_belief = belief
        threshold = (
            scenario.hard_return_threshold
            if planner is V4Planner.HARD_BELIEF
            else None
        )

    planning_arming_probabilities = (
        scenario.arming_probabilities
        if planner is V4Planner.ACTIVATION_ORACLE
        else scenario.planning_arming_probabilities()
    )
    return belief_commitment_astar(
        scenario.grid,
        current,
        scenario.goal,
        safe_cells=safe,
        hazard_model=scenario.hazard_model,
        arming_probabilities=planning_arming_probabilities,
        initial_belief=current_belief,
        config=BeliefCommitmentAStarConfig(
            recoverability_weight=scenario.recoverability_weight,
            max_hazard_cells=max(16, len(scenario.hazard_model.closures)),
            minimum_return_probability=threshold,
        ),
    )


def _planner_prediction(
    scenario: V4ExecutionScenario,
    planner: V4Planner,
    goal: GridCell,
    *,
    true_active: set[int],
    detector_active: set[int],
    belief: ActivationBelief,
    prior_only_belief: ActivationBelief,
) -> float:
    safe = set(scenario.safe_cells)
    if planner is V4Planner.SHORTEST:
        return float("nan")
    if planner is V4Planner.FIXED_MARGINAL_EXACT:
        return exact_safe_return_probability(
            scenario.grid,
            goal,
            safe,
            _fixed_marginal_hazard(scenario),
            max_hazard_cells=max(16, len(scenario.hazard_model.closures)),
        )
    if planner is V4Planner.ACTIVATION_ORACLE:
        current_belief = _point_belief(true_active)
    elif planner is V4Planner.DETECTOR_AS_TRUTH:
        current_belief = _point_belief(detector_active)
    elif planner is V4Planner.PRIOR_ONLY:
        current_belief = prior_only_belief
    else:
        current_belief = belief
    return expected_safe_return_probability(
        scenario.grid,
        goal,
        safe,
        scenario.hazard_model,
        current_belief,
        max_hazard_cells=max(16, len(scenario.hazard_model.closures)),
    )


def run_v4_execution_trial(
    scenario: V4ExecutionScenario,
    *,
    seed: int,
    planner: V4Planner,
    max_steps: int | None = None,
) -> V4ExecutionRecord:
    """Execute one paired trial with truth hidden from non-oracle planners."""

    scenario.validate()
    true_active: set[int] = set()
    detector_active: set[int] = set()
    belief = ActivationBelief.certain_inactive()
    prior_only = ActivationBelief.certain_inactive()
    path = [scenario.start]
    current = scenario.start
    trigger_occurrences = [0 for _ in scenario.hazard_model.closures]
    trigger_ids_executed: list[int] = []
    detector_observations: list[tuple[int, int, bool]] = []
    observation_count = 0
    planning_calls = 0
    nodes_expanded = 0
    planning_time_ms = 0.0
    step_budget = max_steps or max(
        32,
        scenario.grid.width * scenario.grid.height * 4,
    )

    for _ in range(step_budget):
        if current == scenario.goal:
            break
        result = _plan_next(
            scenario,
            planner,
            current,
            true_active=true_active,
            detector_active=detector_active,
            belief=belief,
            prior_only_belief=prior_only,
        )
        planning_calls += 1
        nodes_expanded += int(result.nodes_expanded)
        planning_time_ms += float(result.planning_time_ms)
        if not result.success or len(result.path) < 2:
            return V4ExecutionRecord(
                scenario=scenario.name,
                seed=seed,
                planner=planner.value,
                mission_success=False,
                path=tuple(path),
                path_length=max(0, len(path) - 1),
                true_armed_set=tuple(sorted(true_active)),
                estimated_armed_set=tuple(sorted(detector_active)),
                trigger_ids_executed=tuple(trigger_ids_executed),
                detector_observations=tuple(detector_observations),
                observation_count=observation_count,
                final_belief_support_size=len(belief.probability_by_active_set),
                final_belief_entropy_bits=belief.entropy_bits(),
                final_true_armed_posterior_probability=belief.probability_by_active_set.get(
                    frozenset(true_active), 0.0
                ),
                predicted_return_probability=float("nan"),
                true_model_return_probability=expected_safe_return_probability(
                    scenario.grid,
                    current,
                    set(scenario.safe_cells),
                    scenario.hazard_model,
                    _point_belief(true_active),
                    max_hazard_cells=max(16, len(scenario.hazard_model.closures)),
                ),
                realized_closure_cells=(),
                return_feasible=False,
                planning_calls=planning_calls,
                nodes_expanded=nodes_expanded,
                planning_time_ms=planning_time_ms,
                protocol_valid=True,
                invalid_reason="",
            )

        neighbor = result.path[1]
        transition = (current, neighbor)
        path.append(neighbor)
        current = neighbor

        for index, closure in enumerate(scenario.hazard_model.closures):
            if closure.trigger != transition:
                continue
            occurrence = trigger_occurrences[index]
            trigger_occurrences[index] += 1
            trigger_ids_executed.append(index)

            if index not in true_active:
                armed = (
                    keyed_uniform(
                        scenario.name,
                        seed,
                        index,
                        "arming",
                        occurrence,
                    )
                    < scenario.arming_probabilities[index]
                )
                if armed:
                    true_active.add(index)

            observation_probability = (
                scenario.detection_sensitivities[index]
                if index in true_active
                else 1.0 - scenario.detection_specificities[index]
            )
            observed_armed = (
                keyed_uniform(
                    scenario.name,
                    seed,
                    index,
                    "observation",
                    occurrence,
                )
                < observation_probability
            )
            observation_count += 1
            detector_observations.append((index, occurrence, observed_armed))

            belief = belief.update_after_trigger_execution(
                index,
                arming_probability=scenario.planning_arming_probabilities()[index],
                observed_armed=observed_armed,
                detection_sensitivity=scenario.planning_detection_sensitivities()[index],
                detection_specificity=scenario.planning_detection_specificities()[index],
            )
            prior_only = prior_only.predict_after_trigger_execution(
                index,
                arming_probability=scenario.planning_arming_probabilities()[index],
            )

            update_latched_detector_estimate(
                detector_active,
                index,
                observed_armed=observed_armed,
            )

    mission_success = current == scenario.goal
    if not mission_success:
        return V4ExecutionRecord(
            scenario=scenario.name,
            seed=seed,
            planner=planner.value,
            mission_success=False,
            path=tuple(path),
            path_length=max(0, len(path) - 1),
            true_armed_set=tuple(sorted(true_active)),
            estimated_armed_set=tuple(sorted(detector_active)),
            trigger_ids_executed=tuple(trigger_ids_executed),
            detector_observations=tuple(detector_observations),
            observation_count=observation_count,
            final_belief_support_size=len(belief.probability_by_active_set),
            final_belief_entropy_bits=belief.entropy_bits(),
            final_true_armed_posterior_probability=belief.probability_by_active_set.get(
                frozenset(true_active), 0.0
            ),
            predicted_return_probability=float("nan"),
            true_model_return_probability=expected_safe_return_probability(
                scenario.grid,
                current,
                set(scenario.safe_cells),
                scenario.hazard_model,
                _point_belief(true_active),
                max_hazard_cells=max(16, len(scenario.hazard_model.closures)),
            ),
            realized_closure_cells=(),
            return_feasible=False,
            planning_calls=planning_calls,
            nodes_expanded=nodes_expanded,
            planning_time_ms=planning_time_ms,
            protocol_valid=False,
            invalid_reason="step_budget_exceeded",
        )

    true_model_return_probability = expected_safe_return_probability(
        scenario.grid,
        scenario.goal,
        set(scenario.safe_cells),
        scenario.hazard_model,
        _point_belief(true_active),
        max_hazard_cells=max(16, len(scenario.hazard_model.closures)),
    )

    closed_cells = {
        scenario.hazard_model.closures[index].closure_cell
        for index in true_active
        if keyed_uniform(scenario.name, seed, index, "closure", 0)
        < scenario.hazard_model.closures[index].closure_probability
    }
    return_probability = exact_scenario_safe_return_probability(
        scenario.grid,
        scenario.goal,
        set(scenario.safe_cells),
        TopologyScenarioBelief(
            (ClosureScenario(frozenset(closed_cells), 1.0),)
        ),
    )
    prediction = _planner_prediction(
        scenario,
        planner,
        scenario.goal,
        true_active=true_active,
        detector_active=detector_active,
        belief=belief,
        prior_only_belief=prior_only,
    )

    return V4ExecutionRecord(
        scenario=scenario.name,
        seed=seed,
        planner=planner.value,
        mission_success=True,
        path=tuple(path),
        path_length=max(0, len(path) - 1),
        true_armed_set=tuple(sorted(true_active)),
        estimated_armed_set=tuple(sorted(detector_active)),
        trigger_ids_executed=tuple(trigger_ids_executed),
        detector_observations=tuple(detector_observations),
        observation_count=observation_count,
        final_belief_support_size=len(belief.probability_by_active_set),
        final_belief_entropy_bits=belief.entropy_bits(),
        final_true_armed_posterior_probability=belief.probability_by_active_set.get(
            frozenset(true_active), 0.0
        ),
        predicted_return_probability=prediction,
        true_model_return_probability=true_model_return_probability,
        realized_closure_cells=tuple(sorted(closed_cells)),
        return_feasible=return_probability >= 1.0,
        planning_calls=planning_calls,
        nodes_expanded=nodes_expanded,
        planning_time_ms=planning_time_ms,
        protocol_valid=True,
        invalid_reason="",
    )
