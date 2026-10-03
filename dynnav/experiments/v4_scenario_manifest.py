"""Frozen V4 scenario manifests for partially observed topology hazards.

This module generates scenario specifications only. It does not execute any
planner or inspect comparative outcomes. The emitted JSON manifests are the
authoritative pre-outcome description of the V4 development, validation and
held-out topology suites.
"""

from __future__ import annotations

import json
import random
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.v4_belief_execution import V4ExecutionScenario
from dynnav.planners.grid_map import GridCell, GridMap

V4_DEVELOPMENT_SEED = 2026100301
V4_VALIDATION_SEED = 2026100302
V4_HELDOUT_SEED = 2026100303

NON_NULL_ARMING = (0.4, 0.7, 1.0)
NON_NULL_CLOSURE = (0.25, 0.50, 0.80)


@dataclass(frozen=True)
class FrozenV4HazardSpec:
    trigger: tuple[GridCell, GridCell]
    closure_cell: GridCell
    arming_probability: float
    closure_probability: float

    def validate(self) -> None:
        if not 0.0 <= self.arming_probability <= 1.0:
            raise ValueError("arming_probability must be in [0, 1]")
        if not 0.0 <= self.closure_probability <= 1.0:
            raise ValueError("closure_probability must be in [0, 1]")


@dataclass(frozen=True)
class FrozenV4ScenarioSpec:
    scenario_id: str
    family: str
    width: int
    height: int
    obstacles: tuple[GridCell, ...]
    start: GridCell
    goal: GridCell
    safe_cells: tuple[GridCell, ...]
    hazards: tuple[FrozenV4HazardSpec, ...]
    notes: str = ""

    def grid(self) -> GridMap:
        return GridMap.from_obstacles(
            self.width,
            self.height,
            obstacles=self.obstacles,
        )

    def validate(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id cannot be empty")
        if not self.family:
            raise ValueError("family cannot be empty")
        grid = self.grid()
        if not grid.in_bounds(self.start) or not grid.passable(self.start):
            raise ValueError("start must be free and in bounds")
        if not grid.in_bounds(self.goal) or not grid.passable(self.goal):
            raise ValueError("goal must be free and in bounds")
        if not self.safe_cells:
            raise ValueError("safe_cells cannot be empty")
        for cell in self.safe_cells:
            if not grid.in_bounds(cell) or not grid.passable(cell):
                raise ValueError(f"safe cell must be free and in bounds: {cell}")
        if not self.hazards:
            raise ValueError("scenario must contain at least one hazard")
        closures: list[CommitmentClosure] = []
        for hazard in self.hazards:
            hazard.validate()
            closures.append(
                CommitmentClosure(
                    trigger=hazard.trigger,
                    closure_cell=hazard.closure_cell,
                    closure_probability=hazard.closure_probability,
                )
            )
        CommitmentHazardModel(tuple(closures)).validate(grid)
        if not _can_reach(grid, self.start, {self.goal}):
            raise ValueError("scenario has no start-to-goal path")
        _validate_family_contract(self)

    def to_execution_scenario(
        self,
        *,
        sensitivity: float,
        specificity: float,
        recoverability_weight: float = 8.0,
        hard_return_threshold: float = 0.90,
    ) -> V4ExecutionScenario:
        self.validate()
        grid = self.grid()
        model = CommitmentHazardModel(
            tuple(
                CommitmentClosure(
                    trigger=hazard.trigger,
                    closure_cell=hazard.closure_cell,
                    closure_probability=hazard.closure_probability,
                )
                for hazard in self.hazards
            )
        )
        return V4ExecutionScenario(
            name=self.scenario_id,
            grid=grid,
            start=self.start,
            goal=self.goal,
            safe_cells=frozenset(self.safe_cells),
            hazard_model=model,
            arming_probabilities=tuple(
                hazard.arming_probability for hazard in self.hazards
            ),
            detection_sensitivities=(float(sensitivity),) * len(self.hazards),
            detection_specificities=(float(specificity),) * len(self.hazards),
            recoverability_weight=recoverability_weight,
            hard_return_threshold=hard_return_threshold,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _cell(value: list[int] | tuple[int, int]) -> GridCell:
    return int(value[0]), int(value[1])


def scenario_from_dict(payload: dict[str, object]) -> FrozenV4ScenarioSpec:
    hazards = tuple(
        FrozenV4HazardSpec(
            trigger=(
                _cell(item["trigger"][0]),  # type: ignore[index]
                _cell(item["trigger"][1]),  # type: ignore[index]
            ),
            closure_cell=_cell(item["closure_cell"]),  # type: ignore[index]
            arming_probability=float(item["arming_probability"]),  # type: ignore[index]
            closure_probability=float(item["closure_probability"]),  # type: ignore[index]
        )
        for item in payload["hazards"]  # type: ignore[index]
    )
    spec = FrozenV4ScenarioSpec(
        scenario_id=str(payload["scenario_id"]),
        family=str(payload["family"]),
        width=int(payload["width"]),
        height=int(payload["height"]),
        obstacles=tuple(_cell(cell) for cell in payload["obstacles"]),  # type: ignore[index]
        start=_cell(payload["start"]),  # type: ignore[arg-type]
        goal=_cell(payload["goal"]),  # type: ignore[arg-type]
        safe_cells=tuple(_cell(cell) for cell in payload["safe_cells"]),  # type: ignore[index]
        hazards=hazards,
        notes=str(payload.get("notes", "")),
    )
    spec.validate()
    return spec


def write_manifest(
    scenarios: tuple[FrozenV4ScenarioSpec, ...],
    path: str | Path,
    *,
    split: str,
    seed: int,
) -> None:
    for scenario in scenarios:
        scenario.validate()
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": "EXPERIMENT_PROTOCOL_V4.md",
        "split": split,
        "generator_seed": seed,
        "scenario_count": len(scenarios),
        "families": sorted({scenario.family for scenario in scenarios}),
        "scenarios": [scenario.to_dict() for scenario in scenarios],
    }
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_manifest(path: str | Path) -> tuple[FrozenV4ScenarioSpec, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    scenarios = tuple(
        scenario_from_dict(item)
        for item in payload["scenarios"]
    )
    if len(scenarios) != int(payload["scenario_count"]):
        raise ValueError("scenario_count does not match manifest contents")
    return scenarios


def _obstacles(width: int, height: int, free: set[GridCell]) -> tuple[GridCell, ...]:
    return tuple(
        sorted(
            (x, y)
            for x in range(width)
            for y in range(height)
            if (x, y) not in free
        )
    )


def _can_reach(
    grid: GridMap,
    start: GridCell,
    targets: set[GridCell],
    *,
    extra_blocked: set[GridCell] | None = None,
) -> bool:
    blocked = set(extra_blocked or ())
    if start in blocked or not grid.passable(start):
        return False
    queue: deque[GridCell] = deque([start])
    reached = {start}
    while queue:
        current = queue.popleft()
        if current in targets:
            return True
        for neighbor in grid.neighbors4(current):
            if neighbor in blocked or neighbor in reached:
                continue
            reached.add(neighbor)
            queue.append(neighbor)
    return False


def _draw_non_null(rng: random.Random) -> tuple[float, float]:
    return rng.choice(NON_NULL_ARMING), rng.choice(NON_NULL_CLOSURE)


def _family_f1(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    width, height, y = 9, 5, 2
    detour_y = 1 if index % 2 == 0 else 3
    free = {(x, y) for x in range(width)}
    free.update((x, detour_y) for x in range(4, 8))
    free.update({(4, y), (4, detour_y), (7, y), (7, detour_y)})
    q, p = _draw_non_null(rng)
    return FrozenV4ScenarioSpec(
        scenario_id,
        "F1_bridge_detour",
        width,
        height,
        _obstacles(width, height, free),
        (0, y),
        (8, y),
        ((0, y),),
        (
            FrozenV4HazardSpec(
                trigger=((4, y), (5, y)),
                closure_cell=(2, y),
                arming_probability=q,
                closure_probability=p,
            ),
        ),
        "Short branch arms a latent closure of the unique return bridge; the detour avoids that trigger.",
    )


def _family_f2(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    width, height = 9, 5
    free = {(x, 2) for x in range(0, 5)} | {(x, 2) for x in range(7, 9)}
    free.update((x, 1) for x in range(4, 8))
    free.update((x, 3) for x in range(4, 8))
    free.update({(4, 1), (4, 2), (4, 3), (7, 1), (7, 2), (7, 3)})
    q1, p1 = _draw_non_null(rng)
    q2, p2 = _draw_non_null(rng)
    while (q2, p2) == (q1, p1):
        q2, p2 = _draw_non_null(rng)
    return FrozenV4ScenarioSpec(
        scenario_id,
        "F2_asymmetric_fork",
        width,
        height,
        _obstacles(width, height, free),
        (0, 2),
        (8, 2),
        ((0, 2),),
        (
            FrozenV4HazardSpec(((4, 2), (4, 1)), (1, 2), q1, p1),
            FrozenV4HazardSpec(((4, 2), (4, 3)), (2, 2), q2, p2),
        ),
        "Upper and lower route choices arm different return-critical hazards.",
    )


def _family_f3(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    width, height = 7, 5
    free = {(0, 2), (1, 2), (5, 2), (6, 2)}
    free.update((x, 1) for x in range(1, 6))
    free.update((x, 3) for x in range(1, 6))
    free.update({(1, 1), (1, 3), (5, 1), (5, 3)})
    q1, p1 = _draw_non_null(rng)
    q2, p2 = _draw_non_null(rng)
    return FrozenV4ScenarioSpec(
        scenario_id,
        "F3_redundant_loop",
        width,
        height,
        _obstacles(width, height, free),
        (0, 2),
        (6, 2),
        ((0, 2),),
        (
            FrozenV4HazardSpec(((5, 1), (5, 2)), (3, 1), q1, p1),
            FrozenV4HazardSpec(((5, 3), (5, 2)), (3, 3), q2, p2),
        ),
        "Two redundant return corridors; either single corridor closure is survivable.",
    )


def _family_f4(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    width, height = 9, 7
    free = {(x, 3) for x in range(0, 4)}
    free.update({(3, 2), (3, 4)})
    free.update((x, 2) for x in range(3, 6))
    free.update((x, 4) for x in range(3, 6))
    free.update((x, y) for x in range(5, 9) for y in range(2, 5))
    q1, p1 = _draw_non_null(rng)
    q2, p2 = _draw_non_null(rng)
    return FrozenV4ScenarioSpec(
        scenario_id,
        "F4_chamber_multitrigger",
        width,
        height,
        _obstacles(width, height, free),
        (0, 3),
        (8, 3),
        ((0, 3),),
        (
            FrozenV4HazardSpec(((4, 2), (5, 2)), (2, 3), q1, p1),
            FrozenV4HazardSpec(((4, 4), (5, 4)), (1, 3), q2, p2),
        ),
        "Different entry histories reach the same chamber while arming different latent hazards.",
    )


def _family_f5(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    width, height = 7, 5
    free = {(0, 2), (1, 2), (5, 2), (6, 2)}
    free.update((x, 1) for x in range(1, 6))
    free.update((x, 3) for x in range(1, 6))
    free.update({(1, 1), (1, 3), (5, 1), (5, 3)})
    q1, p1 = _draw_non_null(rng)
    q2, p2 = _draw_non_null(rng)
    return FrozenV4ScenarioSpec(
        scenario_id,
        "F5_parallel_joint_cut",
        width,
        height,
        _obstacles(width, height, free),
        (0, 2),
        (6, 2),
        ((0, 2),),
        (
            FrozenV4HazardSpec(((4, 1), (5, 1)), (3, 1), q1, p1),
            FrozenV4HazardSpec(((4, 3), (5, 3)), (3, 3), q2, p2),
        ),
        "The two closure cells form a joint cut: either alone preserves return, both together disconnect.",
    )


def _family_f6(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    modules = 1 + (index % 3)
    depths = tuple(1 + ((index + j) % 2) for j in range(modules))
    directions = tuple(1 if (index + j) % 2 == 0 else -1 for j in range(modules))
    max_depth = max(depths)
    main_y = max_depth
    height = 2 * max_depth + 1
    width = 5 * modules + 1
    free = {(x, main_y) for x in range(width)}
    hazards: list[FrozenV4HazardSpec] = []

    for module, (depth, direction) in enumerate(zip(depths, directions, strict=True)):
        base = 5 * module
        critical_a = (base + 1, main_y)
        critical_b = (base + 2, main_y)
        source = (base + 3, main_y)
        direct_mid = (base + 4, main_y)
        target = (base + 5, main_y)
        detour_y = main_y + direction * depth
        step = 1 if detour_y > main_y else -1
        for y in range(main_y, detour_y + step, step):
            free.add((source[0], y))
            free.add((target[0], y))
        free.add((direct_mid[0], detour_y))

        q1, p1 = _draw_non_null(rng)
        q2, p2 = _draw_non_null(rng)
        hazards.extend(
            (
                FrozenV4HazardSpec((source, direct_mid), critical_a, q1, p1),
                FrozenV4HazardSpec(
                    (source, (source[0], main_y + direction)),
                    critical_b,
                    q2,
                    p2,
                ),
            )
        )

    return FrozenV4ScenarioSpec(
        scenario_id,
        "F6_unavoidable_choice",
        width,
        height,
        _obstacles(width, height, free),
        (0, main_y),
        (width - 1, main_y),
        ((0, main_y),),
        tuple(hazards),
        "Each serial module requires choosing between hazard-arming route alternatives.",
    )


def _family_f7(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    width, height = 9, 5
    free: set[GridCell] = set()
    free.update((x, 1) for x in range(0, 7))
    free.update((x, 3) for x in range(0, 7))
    free.update((x, 2) for x in range(2, 9))
    free.update({(2, 1), (2, 3), (6, 1), (6, 3)})
    q1, p1 = _draw_non_null(rng)
    q2, p2 = _draw_non_null(rng)
    return FrozenV4ScenarioSpec(
        scenario_id,
        "F7_multiple_safe_regions",
        width,
        height,
        _obstacles(width, height, free),
        (2, 2),
        (8, 2),
        ((0, 1), (0, 3)),
        (
            FrozenV4HazardSpec(((3, 2), (4, 2)), (3, 1), q1, p1),
            FrozenV4HazardSpec(((4, 2), (5, 2)), (3, 3), q2, p2),
        ),
        "Two safe regions remain candidates; closures can remove access to one without necessarily removing the other.",
    )


def _family_f8(rng: random.Random, index: int, scenario_id: str) -> FrozenV4ScenarioSpec:
    width, height, y = 9, 5, 2
    free = {(x, y) for x in range(width)}
    free.add((5, 1))
    subtype = index % 3
    if subtype == 0:
        q, p = 0.0, rng.choice(NON_NULL_CLOSURE)
        closure = (3, y)
        note = "Null control: arming probability q=0."
    elif subtype == 1:
        q, p = rng.choice(NON_NULL_ARMING), 0.0
        closure = (3, y)
        note = "Null control: conditional closure probability p=0."
    else:
        q, p = _draw_non_null(rng)
        closure = (5, 1)
        note = "History-irrelevant control: closure affects only a dead-end spur."

    return FrozenV4ScenarioSpec(
        scenario_id,
        "F8_null_control",
        width,
        height,
        _obstacles(width, height, free),
        (0, y),
        (8, y),
        ((0, y),),
        (
            FrozenV4HazardSpec(
                ((4, y), (5, y)),
                closure,
                q,
                p,
            ),
        ),
        note,
    )


_FAMILY_BUILDERS = (
    _family_f1,
    _family_f2,
    _family_f3,
    _family_f4,
    _family_f5,
    _family_f6,
    _family_f7,
    _family_f8,
)


def _validate_family_contract(spec: FrozenV4ScenarioSpec) -> None:
    grid = spec.grid()
    safe = set(spec.safe_cells)

    if spec.family in {"F3_redundant_loop", "F5_parallel_joint_cut"}:
        if len(spec.hazards) != 2:
            raise ValueError(f"{spec.family} requires exactly two hazards")
        first = spec.hazards[0].closure_cell
        second = spec.hazards[1].closure_cell
        if not _can_reach(grid, spec.goal, safe, extra_blocked={first}):
            raise ValueError(f"{spec.family}: first closure alone must preserve return")
        if not _can_reach(grid, spec.goal, safe, extra_blocked={second}):
            raise ValueError(f"{spec.family}: second closure alone must preserve return")
        if _can_reach(grid, spec.goal, safe, extra_blocked={first, second}):
            raise ValueError(f"{spec.family}: joint closures must disconnect return")

    if spec.family == "F7_multiple_safe_regions" and len(spec.safe_cells) < 2:
        raise ValueError("F7 requires multiple safe regions")

    if spec.family == "F8_null_control":
        hazard = spec.hazards[0]
        if hazard.arming_probability > 0.0 and hazard.closure_probability > 0.0:
            if not _can_reach(
                grid,
                spec.goal,
                safe,
                extra_blocked={hazard.closure_cell},
            ):
                raise ValueError("F8 nonzero hazard must be return-irrelevant")


def generate_v4_suite(
    *,
    split: str,
    seed: int,
    scenarios_per_family: int,
) -> tuple[FrozenV4ScenarioSpec, ...]:
    if split not in {"development", "validation", "heldout"}:
        raise ValueError("split must be development, validation or heldout")
    if scenarios_per_family < 1:
        raise ValueError("scenarios_per_family must be positive")

    rng = random.Random(seed)
    scenarios: list[FrozenV4ScenarioSpec] = []
    for family_index, builder in enumerate(_FAMILY_BUILDERS, start=1):
        for scenario_index in range(scenarios_per_family):
            scenario_id = (
                f"v4_{split}_f{family_index}_{scenario_index:02d}"
            )
            scenario = builder(rng, scenario_index, scenario_id)
            scenario.validate()
            scenarios.append(scenario)
    return tuple(scenarios)


def development_suite() -> tuple[FrozenV4ScenarioSpec, ...]:
    return generate_v4_suite(
        split="development",
        seed=V4_DEVELOPMENT_SEED,
        scenarios_per_family=6,
    )


def validation_suite() -> tuple[FrozenV4ScenarioSpec, ...]:
    return generate_v4_suite(
        split="validation",
        seed=V4_VALIDATION_SEED,
        scenarios_per_family=6,
    )


def heldout_suite() -> tuple[FrozenV4ScenarioSpec, ...]:
    return generate_v4_suite(
        split="heldout",
        seed=V4_HELDOUT_SEED,
        scenarios_per_family=12,
    )
