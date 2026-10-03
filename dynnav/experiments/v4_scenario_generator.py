"""Frozen V4 scenario generator for belief-conditioned safe-return experiments.

This module constructs topology-diverse small grid worlds without running any
planner or inspecting any outcome.  The generated manifest is the pre-outcome
experimental object: once committed, publication-facing runs must consume the
manifest rather than regenerate worlds opportunistically.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.v4_belief_execution import V4ExecutionScenario
from dynnav.planners.grid_map import GridCell, GridMap

V4_PROTOCOL = "EXPERIMENT_PROTOCOL_V4.md"
DEVELOPMENT_SEED = 2026100301
VALIDATION_SEED = 2026100302
HELDOUT_SEED = 2026100303

FAMILIES = (
    "bridge_detour",
    "asymmetric_fork",
    "loop_redundant",
    "chamber_multitrigger",
    "parallel_joint_cut",
    "unavoidable_choice",
    "multiple_safe_regions",
    "history_irrelevant",
)

Q_VALUES = (0.4, 0.7, 1.0)
P_VALUES = (0.25, 0.50, 0.80)


@dataclass(frozen=True)
class FrozenScenarioSpec:
    scenario_id: str
    topology_family: str
    width: int
    height: int
    free_cells: tuple[GridCell, ...]
    start: GridCell
    goal: GridCell
    safe_cells: tuple[GridCell, ...]
    hazards: tuple[dict[str, object], ...]
    arming_probabilities: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "topology_family": self.topology_family,
            "width": self.width,
            "height": self.height,
            "free_cells": [list(c) for c in self.free_cells],
            "start": list(self.start),
            "goal": list(self.goal),
            "safe_cells": [list(c) for c in self.safe_cells],
            "hazards": list(self.hazards),
            "arming_probabilities": list(self.arming_probabilities),
        }


def _line(a: GridCell, b: GridCell) -> set[GridCell]:
    ax, ay = a
    bx, by = b
    if ax != bx and ay != by:
        raise ValueError("line endpoints must be axis aligned")
    if ax == bx:
        lo, hi = sorted((ay, by))
        return {(ax, y) for y in range(lo, hi + 1)}
    lo, hi = sorted((ax, bx))
    return {(x, ay) for x in range(lo, hi + 1)}


def _path(*points: GridCell) -> set[GridCell]:
    cells: set[GridCell] = set()
    for a, b in zip(points, points[1:], strict=False):
        cells |= _line(a, b)
    if len(points) == 1:
        cells.add(points[0])
    return cells


def _hazard(
    trigger: tuple[GridCell, GridCell],
    closure_cell: GridCell,
    p: float,
) -> dict[str, object]:
    return {
        "trigger": [list(trigger[0]), list(trigger[1])],
        "closure_cell": list(closure_cell),
        "closure_probability": float(p),
    }


def _spec(
    scenario_id: str,
    family: str,
    width: int,
    height: int,
    free: set[GridCell],
    start: GridCell,
    goal: GridCell,
    safe: set[GridCell],
    hazards: list[dict[str, object]],
    q: list[float],
) -> FrozenScenarioSpec:
    if len(hazards) != len(q):
        raise ValueError("one arming probability required per hazard")
    return FrozenScenarioSpec(
        scenario_id=scenario_id,
        topology_family=family,
        width=width,
        height=height,
        free_cells=tuple(sorted(free)),
        start=start,
        goal=goal,
        safe_cells=tuple(sorted(safe)),
        hazards=tuple(hazards),
        arming_probabilities=tuple(float(v) for v in q),
    )


def _bridge_detour(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 9, 5
    s, g = (0, 2), (8, 2)
    free = _path(s, g) | _path((2, 2), (2, 1), (6, 1), (6, 2))
    p = rng.choice(P_VALUES)
    q = rng.choice(Q_VALUES)
    hazards = [_hazard(((4, 2), (5, 2)), (2, 2), p)]
    return _spec(sid, "bridge_detour", w, h, free, s, g, {s}, hazards, [q])


def _asymmetric_fork(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 9, 7
    s, g = (0, 3), (8, 3)
    free = _path(s, (2, 3))
    free |= _path((2, 3), (2, 1), (6, 1), (6, 3), g)
    free |= _path((2, 3), (2, 5), (6, 5), (6, 3))
    p1, p2 = rng.sample(P_VALUES, 2)
    q1, q2 = rng.choice(Q_VALUES), rng.choice(Q_VALUES)
    hazards = [
        _hazard(((2, 3), (2, 2)), (1, 3), p1),
        _hazard(((2, 3), (2, 4)), (1, 3), p2),
    ]
    return _spec(sid, "asymmetric_fork", w, h, free, s, g, {s}, hazards, [q1, q2])


def _loop_redundant(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 10, 7
    s, g = (0, 3), (9, 3)
    free = _path(s, (2, 3))
    free |= _path((2, 3), (2, 1), (7, 1), (7, 3), g)
    free |= _path((2, 3), (2, 5), (7, 5), (7, 3))
    p = rng.choice(P_VALUES)
    q1, q2 = rng.choice(Q_VALUES), rng.choice(Q_VALUES)
    hazards = [
        _hazard(((4, 1), (5, 1)), (3, 1), p),
        _hazard(((4, 5), (5, 5)), (3, 5), p),
    ]
    return _spec(sid, "loop_redundant", w, h, free, s, g, {s}, hazards, [q1, q2])


def _chamber_multitrigger(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 10, 7
    s, g = (0, 3), (9, 3)
    free = _path(s, (3, 3)) | _path((6, 3), g)
    free |= {(x, y) for x in range(3, 7) for y in range(1, 6)}
    p1, p2 = rng.choice(P_VALUES), rng.choice(P_VALUES)
    hazards = [
        _hazard(((3, 3), (3, 2)), (2, 3), p1),
        _hazard(((3, 3), (4, 3)), (2, 3), p2),
    ]
    return _spec(
        sid, "chamber_multitrigger", w, h, free, s, g, {s}, hazards,
        [rng.choice(Q_VALUES), rng.choice(Q_VALUES)],
    )


def _parallel_joint_cut(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 10, 7
    s, g = (0, 3), (9, 3)
    free = _path(s, (2, 3))
    free |= _path((2, 3), (2, 1), (7, 1), (7, 3), g)
    free |= _path((2, 3), (2, 5), (7, 5), (7, 3))
    p = rng.choice(P_VALUES)
    hazards = [
        _hazard(((6, 1), (7, 1)), (4, 1), p),
        _hazard(((6, 5), (7, 5)), (4, 5), p),
    ]
    return _spec(
        sid, "parallel_joint_cut", w, h, free, s, g, {s}, hazards,
        [rng.choice(Q_VALUES), rng.choice(Q_VALUES)],
    )


def _unavoidable_choice(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 11, 7
    s, g = (0, 3), (10, 3)
    free = _path(s, (3, 3))
    free |= _path((3, 3), (3, 1), (6, 1), (6, 3))
    free |= _path((3, 3), (3, 5), (6, 5), (6, 3))
    free |= _path((6, 3), g)
    p1, p2 = rng.sample(P_VALUES, 2)
    hazards = [
        _hazard(((3, 3), (3, 2)), (1, 3), p1),
        _hazard(((3, 3), (3, 4)), (2, 3), p2),
    ]
    return _spec(
        sid, "unavoidable_choice", w, h, free, s, g, {s}, hazards,
        [rng.choice(Q_VALUES), rng.choice(Q_VALUES)],
    )


def _multiple_safe_regions(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 11, 7
    s, g = (5, 3), (10, 3)
    safe_a, safe_b = (0, 1), (0, 5)
    free = _path(safe_a, (3, 1), (3, 3), s, g)
    free |= _path(safe_b, (3, 5), (3, 3))
    p1, p2 = rng.choice(P_VALUES), rng.choice(P_VALUES)
    hazards = [
        _hazard(((6, 3), (7, 3)), (2, 1), p1),
        _hazard(((7, 3), (8, 3)), (2, 5), p2),
    ]
    return _spec(
        sid, "multiple_safe_regions", w, h, free, s, g, {safe_a, safe_b}, hazards,
        [rng.choice(Q_VALUES), rng.choice(Q_VALUES)],
    )


def _history_irrelevant(rng: random.Random, sid: str) -> FrozenScenarioSpec:
    w, h = 9, 5
    s, g = (0, 2), (8, 2)
    free = _path(s, g) | _path((3, 2), (3, 1), (5, 1), (5, 2))
    # Closure is deliberately off the only return-critical stem; half of these
    # controls also use p=0 or q=0 at manifest generation time.
    closure = (4, 1)
    p = 0.0 if rng.random() < 0.5 else rng.choice(P_VALUES)
    q = 0.0 if rng.random() < 0.5 else rng.choice(Q_VALUES)
    hazards = [_hazard(((3, 2), (3, 1)), closure, p)]
    return _spec(sid, "history_irrelevant", w, h, free, s, g, {s}, hazards, [q])


_BUILDERS = {
    "bridge_detour": _bridge_detour,
    "asymmetric_fork": _asymmetric_fork,
    "loop_redundant": _loop_redundant,
    "chamber_multitrigger": _chamber_multitrigger,
    "parallel_joint_cut": _parallel_joint_cut,
    "unavoidable_choice": _unavoidable_choice,
    "multiple_safe_regions": _multiple_safe_regions,
    "history_irrelevant": _history_irrelevant,
}


def generate_v4_specs(*, seed: int, scenarios_per_family: int) -> tuple[FrozenScenarioSpec, ...]:
    if scenarios_per_family < 1:
        raise ValueError("scenarios_per_family must be positive")
    rng = random.Random(seed)
    specs: list[FrozenScenarioSpec] = []
    for family in FAMILIES:
        builder = _BUILDERS[family]
        for index in range(scenarios_per_family):
            sid = f"{family}_{index:02d}"
            specs.append(builder(rng, sid))
    return tuple(specs)


def heldout_v4_specs() -> tuple[FrozenScenarioSpec, ...]:
    return generate_v4_specs(seed=HELDOUT_SEED, scenarios_per_family=12)


def development_v4_specs() -> tuple[FrozenScenarioSpec, ...]:
    return generate_v4_specs(seed=DEVELOPMENT_SEED, scenarios_per_family=6)


def validation_v4_specs() -> tuple[FrozenScenarioSpec, ...]:
    return generate_v4_specs(seed=VALIDATION_SEED, scenarios_per_family=6)


def spec_to_scenario(
    spec: FrozenScenarioSpec,
    *,
    sensitivity: float,
    specificity: float,
) -> V4ExecutionScenario:
    free = set(spec.free_cells)
    obstacles = {
        (x, y)
        for x in range(spec.width)
        for y in range(spec.height)
        if (x, y) not in free
    }
    grid = GridMap.from_obstacles(spec.width, spec.height, obstacles=obstacles)
    closures: list[CommitmentClosure] = []
    for raw in spec.hazards:
        trigger_raw = raw["trigger"]
        trigger = (
            tuple(trigger_raw[0]),
            tuple(trigger_raw[1]),
        )
        closures.append(
            CommitmentClosure(
                trigger=trigger,
                closure_cell=tuple(raw["closure_cell"]),
                closure_probability=float(raw["closure_probability"]),
            )
        )
    model = CommitmentHazardModel(tuple(closures))
    scenario = V4ExecutionScenario(
        name=spec.scenario_id,
        grid=grid,
        start=spec.start,
        goal=spec.goal,
        safe_cells=frozenset(spec.safe_cells),
        hazard_model=model,
        arming_probabilities=spec.arming_probabilities,
        detection_sensitivities=(float(sensitivity),) * len(closures),
        detection_specificities=(float(specificity),) * len(closures),
    )
    scenario.validate()
    return scenario


def manifest_payload(
    specs: tuple[FrozenScenarioSpec, ...],
    *,
    split: str,
    generator_seed: int,
) -> dict[str, object]:
    scenarios = [spec.to_dict() for spec in specs]
    canonical = json.dumps(scenarios, sort_keys=True, separators=(",", ":")).encode()
    return {
        "protocol": V4_PROTOCOL,
        "split": split,
        "generator_seed": generator_seed,
        "scenario_count": len(specs),
        "topology_families": list(FAMILIES),
        "scenario_payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "scenarios": scenarios,
    }


def write_manifest(
    path: str | Path,
    specs: tuple[FrozenScenarioSpec, ...],
    *,
    split: str,
    generator_seed: int,
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            manifest_payload(specs, split=split, generator_seed=generator_seed),
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
