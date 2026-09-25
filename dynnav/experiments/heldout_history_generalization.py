"""Held-out heterogeneous benchmark for history-conditioned return topology.

The development benchmarks use repeated modules with one shared closure
probability.  This module deliberately freezes a different evaluation family:
module counts and per-module probabilities that are not part of the development
sweeps.  The geometry is unchanged so the test isolates probability/history
generalization rather than adding an unrelated navigation difficulty.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from dynnav.commitment_hazard import CommitmentClosure, CommitmentHazardModel
from dynnav.experiments.commitment_execution_benchmark import (
    _activated_indices,
    _realize_after_commitment,
    _state_only_marginal_hazard,
)
from dynnav.experiments.multi_commitment_benchmark import multi_commitment_world
from dynnav.experiments.statistics import paired_binary_effect
from dynnav.planners.commitment_aware_astar import (
    CommitmentAwareAStarConfig,
    CommitmentPlannerMode,
    commitment_aware_astar,
)
from dynnav.planners.commitment_cut_astar import (
    CommitmentCutAStarConfig,
    commitment_cut_astar,
)
from dynnav.planners.commitment_safe_return_astar import (
    SafeReturnConstraintConfig,
    commitment_safe_return_astar,
)
from dynnav.planners.hazard_reliability_astar import (
    HazardReliabilityAStarConfig,
    HazardReliabilityMode,
    hazard_reliability_astar,
)
from dynnav.recoverability import return_failure_probability

HELDOUT_SCENARIOS: dict[str, tuple[float, ...]] = {
    "low_to_high_6": (0.15, 0.25, 0.35, 0.55, 0.75, 0.85),
    "alternating_7": (0.80, 0.20, 0.70, 0.30, 0.60, 0.40, 0.90),
    "mixed_8": (0.10, 0.90, 0.20, 0.80, 0.35, 0.65, 0.45, 0.75),
}


@dataclass(frozen=True)
class HeldoutHistoryRecord:
    scenario: str
    seed: int
    module_count: int
    mean_closure_probability: float
    planner: str
    path_length: int
    activated_closure_count: int
    realized_closure_count: int
    recovery_feasible: bool
    irreversible_failure: bool


def heterogeneous_commitment_world(
    probabilities: tuple[float, ...],
):
    """Create the repeated-module world with a frozen probability per trigger."""
    if not probabilities:
        raise ValueError("probabilities cannot be empty")
    if any(not 0.0 <= probability <= 1.0 for probability in probabilities):
        raise ValueError("all probabilities must be in [0, 1]")

    grid, start, goal, safe, base_model = multi_commitment_world(
        len(probabilities), 0.5
    )
    model = CommitmentHazardModel(
        tuple(
            CommitmentClosure(
                trigger=closure.trigger,
                closure_cell=closure.closure_cell,
                closure_probability=probability,
            )
            for closure, probability in zip(
                base_model.closures, probabilities, strict=True
            )
        )
    )
    return grid, start, goal, safe, model


def run_heldout_history_generalization(
    *,
    seeds: tuple[int, ...] = tuple(range(500)),
    scenarios: dict[str, tuple[float, ...]] | None = None,
    recoverability_weight: float = 8.0,
    safe_return_threshold: float = 0.9,
) -> list[HeldoutHistoryRecord]:
    """Evaluate frozen heterogeneous scenarios with common random numbers."""
    if not seeds:
        raise ValueError("seeds cannot be empty")
    frozen = HELDOUT_SCENARIOS if scenarios is None else scenarios
    if not frozen:
        raise ValueError("scenarios cannot be empty")

    records: list[HeldoutHistoryRecord] = []
    for scenario, probabilities in frozen.items():
        grid, start, goal, safe, model = heterogeneous_commitment_world(probabilities)
        module_count = len(probabilities)

        shortest = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            mode=CommitmentPlannerMode.SHORTEST,
        )
        state_only = hazard_reliability_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard=_state_only_marginal_hazard(model),
            mode=HazardReliabilityMode.SINGLE_RETURN,
            config=HazardReliabilityAStarConfig(
                reliability_weight=recoverability_weight
            ),
        )
        state_only_exact = hazard_reliability_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard=_state_only_marginal_hazard(model),
            mode=HazardReliabilityMode.EXACT_RETURN,
            config=HazardReliabilityAStarConfig(
                reliability_weight=recoverability_weight,
                max_hazard_cells=max(16, len(model.closures)),
            ),
        )
        exact = commitment_aware_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            mode=CommitmentPlannerMode.HISTORY_AWARE,
            config=CommitmentAwareAStarConfig(
                recoverability_weight=recoverability_weight,
                max_hazard_cells=max(16, module_count),
            ),
        )
        cut = commitment_cut_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            config=CommitmentCutAStarConfig(
                recoverability_weight=recoverability_weight
            ),
        )
        hard = commitment_safe_return_astar(
            grid,
            start,
            goal,
            safe_cells=safe,
            hazard_model=model,
            config=SafeReturnConstraintConfig(
                minimum_return_probability=safe_return_threshold,
                max_hazard_cells=max(16, module_count),
            ),
        )

        plans = {
            "shortest": shortest,
            "state_only_single": state_only,
            "state_only_exact": state_only_exact,
            "history_exact": exact,
            "history_cut": cut,
            f"hard_return_{safe_return_threshold:g}": hard,
        }
        for planner, result in plans.items():
            if not result.success:
                raise RuntimeError(
                    f"planner {planner} failed in held-out scenario {scenario}"
                )
            path = tuple(result.path)
            active = _activated_indices(model, path)
            for seed in seeds:
                updated, realized = _realize_after_commitment(
                    grid, goal, model, active, seed
                )
                recovery_infeasible = (
                    return_failure_probability(updated, goal, safe) >= 1.0
                )
                records.append(
                    HeldoutHistoryRecord(
                        scenario=scenario,
                        seed=seed,
                        module_count=module_count,
                        mean_closure_probability=sum(probabilities) / module_count,
                        planner=planner,
                        path_length=result.geometric_length,
                        activated_closure_count=len(active),
                        realized_closure_count=realized,
                        recovery_feasible=not recovery_infeasible,
                        irreversible_failure=recovery_infeasible,
                    )
                )
    return records


def _paired_effect(
    records: list[HeldoutHistoryRecord], scenario: str, proposed: str
) -> dict[str, object]:
    baseline = {
        row.seed: row
        for row in records
        if row.scenario == scenario and row.planner == "shortest"
    }
    candidate = {
        row.seed: row
        for row in records
        if row.scenario == scenario and row.planner == proposed
    }
    common = sorted(set(baseline) & set(candidate))
    if not common:
        raise ValueError("no paired held-out seeds")
    return asdict(
        paired_binary_effect(
            [baseline[seed].irreversible_failure for seed in common],
            [candidate[seed].irreversible_failure for seed in common],
            resamples=5000,
            seed=1701 + len(scenario) + len(proposed),
        )
    )


def summarize_heldout_history_generalization(
    records: list[HeldoutHistoryRecord],
) -> dict[str, object]:
    if not records:
        raise ValueError("records cannot be empty")

    result: dict[str, object] = {}
    scenarios = sorted({row.scenario for row in records})
    planners = sorted({row.planner for row in records})
    for scenario in scenarios:
        result[scenario] = {}
        for planner in planners:
            rows = [
                row
                for row in records
                if row.scenario == scenario and row.planner == planner
            ]
            if not rows:
                continue
            result[scenario][planner] = {
                "trials": len(rows),
                "module_count": rows[0].module_count,
                "path_length": rows[0].path_length,
                "activated_closure_count": rows[0].activated_closure_count,
                "irreversible_failure_rate": sum(
                    row.irreversible_failure for row in rows
                )
                / len(rows),
                "mean_realized_closures": sum(
                    row.realized_closure_count for row in rows
                )
                / len(rows),
            }
        result[scenario]["paired_binary_effects_vs_shortest"] = {
            planner: _paired_effect(records, scenario, planner)
            for planner in planners
            if planner != "shortest"
        }
    return result


def write_heldout_history_generalization_artifacts(
    records: list[HeldoutHistoryRecord], output_dir: str | Path
) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in records)
    with (target / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summarize_heldout_history_generalization(records),
            handle,
            indent=2,
            sort_keys=True,
        )
