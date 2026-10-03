"""Development-only adversarial search for receding-vs-exact belief decisions.

The search samples tiny valid grid worlds and compares the first action selected
by the V4 receding-horizon predictive-belief A* against an exact finite-horizon
observation-contingent policy. It is a falsification tool, not publication
evidence and never reads the held-out V4 manifest.
"""

from __future__ import annotations

import csv
import json
import random
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.activation_belief import ActivationBelief
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.belief_commitment_astar import (
    BeliefCommitmentAStarConfig,
    belief_commitment_astar,
)
from dynnav.planners.exact_belief_policy import (
    ExactBeliefPolicyConfig,
    exact_finite_horizon_belief_policy,
)
from dynnav.planners.grid_map import GridCell, GridMap


@dataclass(frozen=True)
class ExactPolicySearchRecord:
    candidate: int
    seed: int
    width: int
    height: int
    obstacle_count: int
    hazard_count: int
    shortest_distance: int
    horizon: int
    sensitivity: float
    specificity: float
    exact_success: bool
    receding_success: bool
    exact_first_action: GridCell | None
    receding_first_action: GridCell | None
    action_disagreement: bool
    exact_value: float
    receding_first_action_exact_value: float
    first_action_regret: float
    exact_states_evaluated: int
    arming_probabilities: tuple[float, ...]
    closure_probabilities: tuple[float, ...]
    triggers: tuple[tuple[GridCell, GridCell], ...]
    closure_cells: tuple[GridCell, ...]
    obstacles: tuple[GridCell, ...]


def _shortest_distance(
    grid: GridMap,
    start: GridCell,
    goal: GridCell,
) -> int | None:
    queue: deque[tuple[GridCell, int]] = deque([(start, 0)])
    reached = {start}
    while queue:
        cell, distance = queue.popleft()
        if cell == goal:
            return distance
        for neighbor in grid.neighbors4(cell):
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append((neighbor, distance + 1))
    return None


def _random_world(
    rng: random.Random,
) -> tuple[
    GridMap,
    GridCell,
    GridCell,
    CommitmentHazardModel,
    tuple[float, ...],
    tuple[float, ...],
    tuple[float, ...],
    int,
] | None:
    width = 5
    height = 5
    start = (0, 2)
    goal = (4, 2)

    cells = [
        (x, y)
        for x in range(width)
        for y in range(height)
        if (x, y) not in {start, goal}
    ]
    obstacle_count = rng.randint(2, 7)
    obstacles = set(rng.sample(cells, obstacle_count))
    grid = GridMap.from_obstacles(width, height, obstacles=obstacles)
    distance = _shortest_distance(grid, start, goal)
    if distance is None or distance > 6:
        return None

    directed_edges = [
        (cell, neighbor)
        for x in range(width)
        for y in range(height)
        for cell in [(x, y)]
        if grid.passable(cell)
        for neighbor in grid.neighbors4(cell)
    ]
    if len(directed_edges) < 2:
        return None

    hazard_count = rng.choice((1, 2))
    triggers = rng.sample(directed_edges, hazard_count)
    free_cells = [
        (x, y)
        for x in range(width)
        for y in range(height)
        if grid.passable((x, y)) and (x, y) not in {start, goal}
    ]
    if len(free_cells) < hazard_count:
        return None
    closure_cells = rng.sample(free_cells, hazard_count)

    closure_probabilities = tuple(
        rng.choice((0.4, 0.7, 0.9))
        for _ in range(hazard_count)
    )
    arming_probabilities = tuple(
        rng.choice((0.3, 0.5, 0.8, 1.0))
        for _ in range(hazard_count)
    )
    sensor = rng.choice(
        (
            (1.0, 1.0),
            (0.9, 0.9),
            (0.8, 0.8),
            (0.7, 0.95),
            (0.5, 0.5),
        )
    )

    model = CommitmentHazardModel(
        tuple(
            CommitmentClosure(
                trigger=trigger,
                closure_cell=closure_cell,
                closure_probability=closure_probability,
            )
            for trigger, closure_cell, closure_probability in zip(
                triggers,
                closure_cells,
                closure_probabilities,
                strict=True,
            )
        )
    )
    try:
        model.validate(grid)
    except ValueError:
        return None

    horizon = min(8, distance + 3)
    return (
        grid,
        start,
        goal,
        model,
        arming_probabilities,
        (sensor[0],) * hazard_count,
        (sensor[1],) * hazard_count,
        horizon,
    )


def run_exact_policy_search(
    *,
    candidates: int = 100,
    seed: int = 2026100305,
) -> list[ExactPolicySearchRecord]:
    if candidates <= 0:
        raise ValueError("candidates must be positive")

    rng = random.Random(seed)
    records: list[ExactPolicySearchRecord] = []
    attempts = 0
    max_attempts = candidates * 20

    while len(records) < candidates and attempts < max_attempts:
        candidate = len(records)
        attempts += 1
        world = _random_world(rng)
        if world is None:
            continue

        (
            grid,
            start,
            goal,
            model,
            arming_probabilities,
            sensitivities,
            specificities,
            horizon,
        ) = world
        distance = _shortest_distance(grid, start, goal)
        if distance is None:
            continue

        exact = exact_finite_horizon_belief_policy(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            arming_probabilities=arming_probabilities,
            detection_sensitivities=sensitivities,
            detection_specificities=specificities,
            initial_belief=ActivationBelief.certain_inactive(),
            config=ExactBeliefPolicyConfig(
                horizon=horizon,
                recoverability_weight=8.0,
                max_hazards=3,
            ),
        )
        receding = belief_commitment_astar(
            grid,
            start,
            goal,
            safe_cells={start},
            hazard_model=model,
            arming_probabilities=arming_probabilities,
            initial_belief=ActivationBelief.certain_inactive(),
            config=BeliefCommitmentAStarConfig(
                recoverability_weight=8.0,
            ),
        )

        receding_action = (
            receding.path[1]
            if receding.success and len(receding.path) >= 2
            else None
        )
        action_value_map = dict(exact.action_values)
        receding_exact_value = action_value_map.get(
            receding_action,
            float("inf"),
        )
        regret = (
            receding_exact_value - exact.value
            if exact.success and receding_action in action_value_map
            else float("inf")
        )

        records.append(
            ExactPolicySearchRecord(
                candidate=candidate,
                seed=seed,
                width=grid.width,
                height=grid.height,
                obstacle_count=len(grid.obstacles),
                hazard_count=len(model.closures),
                shortest_distance=distance,
                horizon=horizon,
                sensitivity=sensitivities[0],
                specificity=specificities[0],
                exact_success=exact.success,
                receding_success=receding.success,
                exact_first_action=exact.first_action,
                receding_first_action=receding_action,
                action_disagreement=(
                    exact.success
                    and receding.success
                    and exact.first_action != receding_action
                ),
                exact_value=exact.value,
                receding_first_action_exact_value=receding_exact_value,
                first_action_regret=regret,
                exact_states_evaluated=exact.states_evaluated,
                arming_probabilities=arming_probabilities,
                closure_probabilities=tuple(
                    closure.closure_probability for closure in model.closures
                ),
                triggers=tuple(closure.trigger for closure in model.closures),
                closure_cells=tuple(
                    closure.closure_cell for closure in model.closures
                ),
                obstacles=tuple(sorted(grid.obstacles)),
            )
        )

    if len(records) != candidates:
        raise RuntimeError(
            f"generated only {len(records)} valid worlds after {attempts} attempts"
        )
    return records


def summarize_exact_policy_search(
    records: list[ExactPolicySearchRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")

    comparable = [
        row
        for row in records
        if row.exact_success and row.receding_success
    ]
    disagreements = [
        row for row in comparable if row.action_disagreement
    ]
    positive_regret = [
        row
        for row in comparable
        if row.first_action_regret > 1e-9
        and row.first_action_regret != float("inf")
    ]

    return {
        "status": "development_only_not_publication_evidence",
        "candidate_count": len(records),
        "comparable_count": len(comparable),
        "action_disagreement_count": len(disagreements),
        "action_disagreement_rate": (
            len(disagreements) / len(comparable) if comparable else None
        ),
        "positive_first_action_regret_count": len(positive_regret),
        "max_first_action_regret": (
            max(row.first_action_regret for row in positive_regret)
            if positive_regret
            else 0.0
        ),
        "mean_exact_states_evaluated": sum(
            row.exact_states_evaluated for row in records
        )
        / len(records),
    }


def write_exact_policy_search_artifacts(
    records: list[ExactPolicySearchRecord],
    output_dir: str | Path,
) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    rows = [asdict(record) for record in records]
    with (destination / "trials.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    (destination / "summary.json").write_text(
        json.dumps(
            summarize_exact_policy_search(records),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
