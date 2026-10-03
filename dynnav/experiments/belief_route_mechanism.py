"""Development-only route-choice benchmark for V4 latent hazard arming.

This module is intentionally small. It provides a two-corridor world in which
a previous latent hazard can threaten one return corridor and a short final
move can arm a hazard threatening the other corridor. The same geometric state
can therefore rationally select a different route under different beliefs.

The benchmark is for mechanism debugging and falsification. It is not part of
the frozen V4 held-out suite.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.activation_belief import ActivationBelief
from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.planners.belief_commitment_astar import (
    BeliefCommitmentAStarConfig,
    belief_commitment_astar,
)
from dynnav.planners.grid_map import GridMap
from dynnav.recoverability_scenarios import (
    ClosureScenario,
    TopologyScenarioBelief,
    exact_scenario_safe_return_probability,
)


@dataclass(frozen=True)
class BeliefRouteRegime:
    name: str
    prior_arming_probability: float
    sensitivity: float
    specificity: float
    closure_probability: float = 0.8
    downstream_arming_probability: float = 1.0
    recoverability_weight: float = 8.0

    def validate(self) -> None:
        for name, value in (
            ("prior_arming_probability", self.prior_arming_probability),
            ("sensitivity", self.sensitivity),
            ("specificity", self.specificity),
            ("closure_probability", self.closure_probability),
            ("downstream_arming_probability", self.downstream_arming_probability),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.recoverability_weight < 0.0:
            raise ValueError("recoverability_weight must be non-negative")


@dataclass(frozen=True)
class BeliefRouteRecord:
    regime: str
    seed: int
    method: str
    previous_hazard_armed: bool
    observed_armed: bool
    path_length: int
    took_downstream_trigger: bool
    predicted_return_probability: float
    realized_return_feasible: bool
    brier_score: float
    posterior_previous_hazard: float


DEFAULT_REGIMES = (
    BeliefRouteRegime(
        name="medium_correct",
        prior_arming_probability=0.7,
        sensitivity=0.85,
        specificity=0.85,
    ),
    BeliefRouteRegime(
        name="miss_heavy_correct",
        prior_arming_probability=0.7,
        sensitivity=0.70,
        specificity=0.95,
    ),
)


def redundant_corridor_world(
    closure_probability: float = 0.8,
) -> tuple[
    GridMap,
    tuple[int, int],
    tuple[int, int],
    set[tuple[int, int]],
    CommitmentHazardModel,
]:
    """Return the development world used for observation-sensitive route choice."""

    obstacles = {(2, 0), (2, 2), (2, 4)}
    grid = GridMap.from_obstacles(5, 5, obstacles=obstacles)
    current = (3, 2)
    goal = (4, 2)
    safe = {(0, 2)}
    model = CommitmentHazardModel(
        (
            CommitmentClosure(
                trigger=((0, 2), (0, 1)),
                closure_cell=(2, 1),
                closure_probability=closure_probability,
            ),
            CommitmentClosure(
                trigger=(current, goal),
                closure_cell=(2, 3),
                closure_probability=closure_probability,
            ),
        )
    )
    model.validate(grid)
    return grid, current, goal, safe, model


def _uniform(seed: int, *key: object) -> float:
    payload = "|".join((str(seed), *(str(part) for part in key))).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    integer = int.from_bytes(digest[:8], "big")
    return integer / float(2**64)


def _belief_for_method(
    method: str,
    *,
    prior_arming_probability: float,
    observed_armed: bool,
    true_armed: bool,
    sensitivity: float,
    specificity: float,
) -> ActivationBelief:
    predictive = ActivationBelief.certain_inactive().predict_after_trigger_execution(
        0,
        arming_probability=prior_arming_probability,
    )
    if method == "belief":
        return predictive.condition_on_arming_observation(
            0,
            observed_armed=observed_armed,
            detection_sensitivity=sensitivity,
            detection_specificity=specificity,
        )
    if method == "prior_only":
        return predictive
    if method == "detector_as_truth":
        return ActivationBelief.certain_active({0}) if observed_armed else ActivationBelief.certain_inactive()
    if method == "activation_oracle":
        return ActivationBelief.certain_active({0}) if true_armed else ActivationBelief.certain_inactive()
    raise ValueError(f"unknown method: {method}")


def run_belief_route_development_benchmark(
    *,
    regimes: tuple[BeliefRouteRegime, ...] = DEFAULT_REGIMES,
    seeds: tuple[int, ...] = tuple(range(1000)),
) -> list[BeliefRouteRecord]:
    """Run paired latent arming, sensing, planning and future closure trials."""

    if not regimes:
        raise ValueError("regimes cannot be empty")
    if not seeds:
        raise ValueError("seeds cannot be empty")

    records: list[BeliefRouteRecord] = []
    methods = ("activation_oracle", "belief", "prior_only", "detector_as_truth")

    for regime in regimes:
        regime.validate()
        grid, current, goal, safe, model = redundant_corridor_world(
            regime.closure_probability
        )
        for seed in seeds:
            true_armed = (
                _uniform(seed, regime.name, "arming", 0)
                < regime.prior_arming_probability
            )
            observation_probability = (
                regime.sensitivity if true_armed else 1.0 - regime.specificity
            )
            observed = (
                _uniform(seed, regime.name, "observation", 0)
                < observation_probability
            )

            for method in methods:
                belief = _belief_for_method(
                    method,
                    prior_arming_probability=regime.prior_arming_probability,
                    observed_armed=observed,
                    true_armed=true_armed,
                    sensitivity=regime.sensitivity,
                    specificity=regime.specificity,
                )
                result = belief_commitment_astar(
                    grid,
                    current,
                    goal,
                    safe_cells=safe,
                    hazard_model=model,
                    arming_probabilities=(
                        0.0,
                        regime.downstream_arming_probability,
                    ),
                    initial_belief=belief,
                    config=BeliefCommitmentAStarConfig(
                        recoverability_weight=regime.recoverability_weight
                    ),
                )
                if not result.success:
                    raise RuntimeError(f"planner failed for {regime.name}/{method}")

                trigger = model.closures[1].trigger
                took_downstream_trigger = trigger in set(
                    zip(result.path, result.path[1:], strict=False)
                )
                downstream_armed = (
                    took_downstream_trigger
                    and _uniform(seed, regime.name, "arming", 1)
                    < regime.downstream_arming_probability
                )

                true_active: set[int] = set()
                if true_armed:
                    true_active.add(0)
                if downstream_armed:
                    true_active.add(1)

                closed_cells = {
                    model.closures[index].closure_cell
                    for index in true_active
                    if _uniform(seed, regime.name, "closure", index)
                    < model.closures[index].closure_probability
                }
                realized_return = exact_scenario_safe_return_probability(
                    grid,
                    goal,
                    safe,
                    TopologyScenarioBelief(
                        (ClosureScenario(frozenset(closed_cells), 1.0),)
                    ),
                )
                feasible = realized_return >= 1.0
                prediction = result.final_predicted_return_probability

                records.append(
                    BeliefRouteRecord(
                        regime=regime.name,
                        seed=seed,
                        method=method,
                        previous_hazard_armed=true_armed,
                        observed_armed=observed,
                        path_length=result.geometric_length,
                        took_downstream_trigger=took_downstream_trigger,
                        predicted_return_probability=prediction,
                        realized_return_feasible=feasible,
                        brier_score=(prediction - float(feasible)) ** 2,
                        posterior_previous_hazard=belief.probability_armed(0),
                    )
                )
    return records


def summarize_belief_route_records(
    records: list[BeliefRouteRecord],
) -> dict[str, dict[str, dict[str, float]]]:
    summary: dict[str, dict[str, dict[str, float]]] = {}
    groups: dict[tuple[str, str], list[BeliefRouteRecord]] = {}
    for record in records:
        groups.setdefault((record.regime, record.method), []).append(record)

    for (regime, method), group in sorted(groups.items()):
        n = len(group)
        summary.setdefault(regime, {})[method] = {
            "trials": float(n),
            "mean_path_length": sum(row.path_length for row in group) / n,
            "downstream_trigger_rate": sum(
                row.took_downstream_trigger for row in group
            )
            / n,
            "return_infeasible_rate": sum(
                not row.realized_return_feasible for row in group
            )
            / n,
            "mean_predicted_return_probability": sum(
                row.predicted_return_probability for row in group
            )
            / n,
            "brier_score": sum(row.brier_score for row in group) / n,
        }
    return summary


def write_belief_route_artifacts(
    records: list[BeliefRouteRecord],
    output_dir: str | Path,
) -> None:
    if not records:
        raise ValueError("records cannot be empty")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    rows = [asdict(record) for record in records]
    with (destination / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with (destination / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summarize_belief_route_records(records), handle, indent=2, sort_keys=True)

    metadata = {
        "status": "development_only_not_publication_evidence",
        "methods": sorted({record.method for record in records}),
        "regimes": sorted({record.regime for record in records}),
        "seed_count": len({record.seed for record in records}),
        "protocol": "EXPERIMENT_PROTOCOL_V4.md",
    }
    with (destination / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
