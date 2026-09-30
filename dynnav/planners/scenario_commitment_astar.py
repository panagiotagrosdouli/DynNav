"""Known-joint augmented-state A* for action-triggered closure scenarios.

This planner is a V2 evaluation reference. It receives the true joint dependence
semantics used by the simulator and therefore is not an implementable baseline
when those semantics are unknown. Its purpose is to separate model
misspecification from path-search effects.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass
from enum import Enum
from itertools import product

from dynnav.commitment_hazard import CommitmentHazardModel
from dynnav.planners.grid_map import GridCell, GridMap, manhattan
from dynnav.recoverability_scenarios import (
    ClosureScenario,
    TopologyScenarioBelief,
    exact_scenario_safe_return_probability,
)

AugmentedState = tuple[GridCell, frozenset[int]]


class JointDependenceMode(str, Enum):
    INDEPENDENT = "independent"
    COMMON_CAUSE = "common_cause"
    ANTI_CORRELATED = "anti_correlated"
    PARTIAL_MIXTURE = "partial_mixture"


@dataclass(frozen=True)
class ScenarioCommitmentAStarConfig:
    step_cost: float = 1.0
    recoverability_weight: float = 4.0
    heuristic_weight: float = 1.0
    common_cause_mixture_weight: float = 0.5

    def validate(self) -> None:
        if self.step_cost <= 0.0:
            raise ValueError("step_cost must be positive")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")
        if self.heuristic_weight < 0.0:
            raise ValueError("heuristic_weight must be non-negative")
        if not 0.0 <= self.common_cause_mixture_weight <= 1.0:
            raise ValueError("common_cause_mixture_weight must be in [0, 1]")


@dataclass(frozen=True)
class ScenarioCommitmentAStarResult:
    path: tuple[GridCell, ...]
    success: bool
    cost: float
    geometric_length: int
    nodes_expanded: int
    planning_time_ms: float
    final_return_probability: float
    minimum_return_probability: float
    activated_hazard_count: int
    dependence: JointDependenceMode


def _activated_after_transition(
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


def _active_cells_and_probabilities(
    model: CommitmentHazardModel,
    active: frozenset[int],
) -> tuple[tuple[GridCell, float], ...]:
    by_cell: dict[GridCell, float] = {}
    for index in active:
        if index < 0 or index >= len(model.closures):
            raise ValueError(f"active hazard index out of range: {index}")
        closure = model.closures[index]
        probability = float(closure.closure_probability)
        existing = by_cell.get(closure.closure_cell)
        if existing is not None and existing != probability:
            raise ValueError(
                "active hazards assign conflicting probabilities "
                f"to {closure.closure_cell}"
            )
        by_cell[closure.closure_cell] = probability
    return tuple(sorted(by_cell.items()))


def _independent_distribution(
    cells: tuple[tuple[GridCell, float], ...],
) -> dict[frozenset[GridCell], float]:
    distribution: dict[frozenset[GridCell], float] = {}
    for flags in product((False, True), repeat=len(cells)):
        closed: set[GridCell] = set()
        probability = 1.0
        for (cell, p_closed), is_closed in zip(cells, flags, strict=True):
            probability *= p_closed if is_closed else 1.0 - p_closed
            if is_closed:
                closed.add(cell)
        if probability > 0.0:
            key = frozenset(closed)
            distribution[key] = distribution.get(key, 0.0) + probability
    return distribution


def _equal_marginal_probability(
    cells: tuple[tuple[GridCell, float], ...],
) -> float:
    if not cells:
        return 0.0
    values = {probability for _, probability in cells}
    if len(values) != 1:
        raise ValueError(
            "selected dependence mode requires equal active closure marginals"
        )
    return next(iter(values))


def _common_cause_distribution(
    cells: tuple[tuple[GridCell, float], ...],
) -> dict[frozenset[GridCell], float]:
    if not cells:
        return {frozenset(): 1.0}
    p = _equal_marginal_probability(cells)
    all_closed = frozenset(cell for cell, _ in cells)
    distribution = {frozenset(): 1.0 - p}
    if p > 0.0:
        distribution[all_closed] = p
    return {key: value for key, value in distribution.items() if value > 0.0}


def _anti_correlated_distribution(
    cells: tuple[tuple[GridCell, float], ...],
) -> dict[frozenset[GridCell], float]:
    if not cells:
        return {frozenset(): 1.0}
    if len(cells) == 1:
        cell, p = cells[0]
        distribution = {
            frozenset(): 1.0 - p,
            frozenset({cell}): p,
        }
        return {key: value for key, value in distribution.items() if value > 0.0}
    if len(cells) != 2:
        raise ValueError(
            "anti-correlated reference currently supports at most two active cells"
        )
    p = _equal_marginal_probability(cells)
    if 2.0 * p > 1.0 + 1e-12:
        raise ValueError(
            "mutually exclusive equal-marginal closures require 2*p <= 1"
        )
    first, second = cells[0][0], cells[1][0]
    distribution = {
        frozenset(): max(0.0, 1.0 - 2.0 * p),
        frozenset({first}): p,
        frozenset({second}): p,
    }
    return {key: value for key, value in distribution.items() if value > 0.0}


def _mix_distributions(
    independent: dict[frozenset[GridCell], float],
    common_cause: dict[frozenset[GridCell], float],
    common_cause_weight: float,
) -> dict[frozenset[GridCell], float]:
    distribution: dict[frozenset[GridCell], float] = {}
    for scenario, probability in independent.items():
        distribution[scenario] = distribution.get(scenario, 0.0) + (
            1.0 - common_cause_weight
        ) * probability
    for scenario, probability in common_cause.items():
        distribution[scenario] = distribution.get(scenario, 0.0) + (
            common_cause_weight * probability
        )
    return {
        scenario: probability
        for scenario, probability in distribution.items()
        if probability > 0.0
    }


def scenario_belief_for_active(
    model: CommitmentHazardModel,
    active: frozenset[int],
    dependence: JointDependenceMode,
    *,
    common_cause_mixture_weight: float = 0.5,
) -> TopologyScenarioBelief:
    """Construct the exact joint closure law for a frozen dependence mode."""

    if not 0.0 <= common_cause_mixture_weight <= 1.0:
        raise ValueError("common_cause_mixture_weight must be in [0, 1]")
    cells = _active_cells_and_probabilities(model, active)

    if dependence is JointDependenceMode.INDEPENDENT:
        distribution = _independent_distribution(cells)
    elif dependence is JointDependenceMode.COMMON_CAUSE:
        distribution = _common_cause_distribution(cells)
    elif dependence is JointDependenceMode.ANTI_CORRELATED:
        distribution = _anti_correlated_distribution(cells)
    elif dependence is JointDependenceMode.PARTIAL_MIXTURE:
        distribution = _mix_distributions(
            _independent_distribution(cells),
            _common_cause_distribution(cells),
            common_cause_mixture_weight,
        )
    else:  # pragma: no cover - defensive Enum boundary
        raise ValueError(f"unsupported dependence mode: {dependence}")

    scenarios = tuple(
        ClosureScenario(closed_cells=scenario, probability=probability)
        for scenario, probability in sorted(
            distribution.items(),
            key=lambda item: (len(item[0]), sorted(item[0])),
        )
    )
    return TopologyScenarioBelief(scenarios)


def _return_probability(
    grid: GridMap,
    cell: GridCell,
    safe_cells: set[GridCell],
    model: CommitmentHazardModel,
    active: frozenset[int],
    dependence: JointDependenceMode,
    config: ScenarioCommitmentAStarConfig,
) -> float:
    belief = scenario_belief_for_active(
        model,
        active,
        dependence,
        common_cause_mixture_weight=config.common_cause_mixture_weight,
    )
    return exact_scenario_safe_return_probability(
        grid,
        cell,
        safe_cells,
        belief,
    )


def scenario_commitment_astar(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
    *,
    safe_cells: set[GridCell] | None = None,
    hazard_model: CommitmentHazardModel | None = None,
    dependence: JointDependenceMode = JointDependenceMode.INDEPENDENT,
    config: ScenarioCommitmentAStarConfig | None = None,
    initial_activated_closures: frozenset[int] | None = None,
) -> ScenarioCommitmentAStarResult:
    """Plan with full knowledge of the declared joint closure distribution."""

    grid.validate()
    cfg = config or ScenarioCommitmentAStarConfig()
    cfg.validate()
    safe = set(safe_cells) if safe_cells is not None else {start}
    model = hazard_model or CommitmentHazardModel(())
    model.validate(grid)
    initial_active = frozenset(initial_activated_closures or ())
    for index in initial_active:
        if index < 0 or index >= len(model.closures):
            raise ValueError(f"initial active hazard index out of range: {index}")

    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        raise ValueError("start and goal must be inside the grid")
    if not grid.passable(start) or not grid.passable(goal):
        return ScenarioCommitmentAStarResult(
            (),
            False,
            float("inf"),
            0,
            0,
            0.0,
            0.0,
            0.0,
            len(initial_active),
            dependence,
        )

    initial: AugmentedState = (start, initial_active)
    frontier: list[tuple[float, int, AugmentedState]] = [(0.0, 0, initial)]
    costs: dict[AugmentedState, float] = {initial: 0.0}
    parents: dict[AugmentedState, AugmentedState] = {}
    counter = 0
    nodes_expanded = 0
    t0 = time.perf_counter()

    while frontier:
        _, _, state = heapq.heappop(frontier)
        cell, active = state
        nodes_expanded += 1

        if cell == goal:
            planning_time_ms = (time.perf_counter() - t0) * 1000.0
            states = [state]
            cursor = state
            while cursor in parents:
                cursor = parents[cursor]
                states.append(cursor)
            states.reverse()
            path = tuple(item[0] for item in states)
            probabilities = [
                _return_probability(
                    grid,
                    item_cell,
                    safe,
                    model,
                    item_active,
                    dependence,
                    cfg,
                )
                for item_cell, item_active in states
            ]
            return ScenarioCommitmentAStarResult(
                path=path,
                success=True,
                cost=costs[state],
                geometric_length=max(0, len(path) - 1),
                nodes_expanded=nodes_expanded,
                planning_time_ms=planning_time_ms,
                final_return_probability=probabilities[-1],
                minimum_return_probability=min(probabilities),
                activated_hazard_count=len(states[-1][1]),
                dependence=dependence,
            )

        for neighbor in grid.neighbors4(cell):
            next_active = _activated_after_transition(
                model,
                cell,
                neighbor,
                active,
            )
            next_state: AugmentedState = (neighbor, next_active)
            probability = _return_probability(
                grid,
                neighbor,
                safe,
                model,
                next_active,
                dependence,
                cfg,
            )
            transition = (
                cfg.step_cost
                + cfg.recoverability_weight * (1.0 - probability)
            )
            new_cost = costs[state] + transition
            if new_cost < costs.get(next_state, float("inf")):
                costs[next_state] = new_cost
                parents[next_state] = state
                counter += 1
                priority = (
                    new_cost
                    + cfg.heuristic_weight
                    * cfg.step_cost
                    * manhattan(neighbor, goal)
                )
                heapq.heappush(frontier, (priority, counter, next_state))

    return ScenarioCommitmentAStarResult(
        (),
        False,
        float("inf"),
        0,
        nodes_expanded,
        (time.perf_counter() - t0) * 1000.0,
        0.0,
        0.0,
        len(initial_active),
        dependence,
    )
