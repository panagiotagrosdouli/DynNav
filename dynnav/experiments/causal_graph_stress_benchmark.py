"""G4 randomized trigger-graph recovery stress benchmark.

This benchmark varies treatment propensity, effect strength and sample size
under known randomized assignment. It quantifies when the narrow IPW
trigger-to-closure estimator can recover a sparse injected graph.

It does not claim hidden-confounder identification or general SCM discovery.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from statistics import mean, stdev
from typing import Any

from dynnav.causal_trigger_discovery import (
    TriggerOutcomeRecord,
    discover_trigger_closure_edges,
    estimate_ipw_trigger_effect,
)


_BASE_EFFECTS = {
    ("t0", "c0"): 0.45,
    ("t1", "c2"): 0.30,
    ("t2", "c1"): 0.20,
}


@dataclass(frozen=True)
class CausalGraphStressRecord:
    trials_per_pair: int
    propensity: float
    effect_scale: float
    repetition: int
    precision: float
    recall: float
    false_positives: int
    false_negatives: int
    mean_positive_edge_absolute_error: float


def _run_condition(
    *,
    trials_per_pair: int,
    propensity: float,
    effect_scale: float,
    repetition: int,
    seed: int,
) -> CausalGraphStressRecord:
    if trials_per_pair <= 0:
        raise ValueError("trials_per_pair must be positive")
    if not 0.0 < propensity < 1.0:
        raise ValueError("propensity must lie strictly between 0 and 1")
    if effect_scale <= 0.0:
        raise ValueError("effect_scale must be positive")

    rng = random.Random(seed)
    trigger_ids = ("t0", "t1", "t2")
    closure_ids = ("c0", "c1", "c2")
    baseline = 0.10
    truth = set(_BASE_EFFECTS)
    records: list[TriggerOutcomeRecord] = []

    for trigger_id in trigger_ids:
        for closure_id in closure_ids:
            base_effect = _BASE_EFFECTS.get((trigger_id, closure_id), 0.0)
            effect = base_effect * effect_scale
            if baseline + effect > 1.0:
                raise ValueError("effect scale produces an invalid outcome probability")
            for _ in range(trials_per_pair):
                executed = rng.random() < propensity
                outcome_probability = baseline + effect * float(executed)
                records.append(
                    TriggerOutcomeRecord(
                        trigger_id=trigger_id,
                        closure_id=closure_id,
                        executed=executed,
                        closure_observed=rng.random() < outcome_probability,
                        execution_propensity=propensity,
                    )
                )

    discovered_estimates = discover_trigger_closure_edges(
        records,
        minimum_effect=0.05,
        require_positive_95_interval=True,
    )
    discovered = {
        (estimate.trigger_id, estimate.closure_id)
        for estimate in discovered_estimates
    }
    true_positives = len(discovered & truth)
    false_positives = len(discovered - truth)
    false_negatives = len(truth - discovered)
    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = true_positives / len(truth)

    positive_errors = []
    for pair, base_effect in _BASE_EFFECTS.items():
        estimate = estimate_ipw_trigger_effect(
            records,
            trigger_id=pair[0],
            closure_id=pair[1],
        )
        positive_errors.append(abs(estimate.ate - base_effect * effect_scale))

    return CausalGraphStressRecord(
        trials_per_pair=trials_per_pair,
        propensity=propensity,
        effect_scale=effect_scale,
        repetition=repetition,
        precision=precision,
        recall=recall,
        false_positives=false_positives,
        false_negatives=false_negatives,
        mean_positive_edge_absolute_error=mean(positive_errors),
    )


def run_causal_graph_stress_benchmark(
    *,
    trials_per_pair_grid: tuple[int, ...] = (100, 250, 500, 1000),
    propensities: tuple[float, ...] = (0.2, 0.5, 0.8),
    effect_scales: tuple[float, ...] = (0.5, 1.0, 1.5),
    repetitions: int = 10,
    seed: int = 20260926,
) -> dict[str, object]:
    """Run the frozen randomized graph-recovery stress grid."""

    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    raw: list[dict[str, object]] = []
    condition = 0
    for trials_per_pair in trials_per_pair_grid:
        for propensity in propensities:
            for effect_scale in effect_scales:
                for repetition in range(repetitions):
                    record = _run_condition(
                        trials_per_pair=trials_per_pair,
                        propensity=propensity,
                        effect_scale=effect_scale,
                        repetition=repetition,
                        seed=seed + 1000 + condition * 97 + repetition,
                    )
                    raw.append(asdict(record))
                condition += 1

    grouped: dict[tuple[int, float, float], list[dict[str, object]]] = {}
    for row in raw:
        key = (
            int(row["trials_per_pair"]),
            float(row["propensity"]),
            float(row["effect_scale"]),
        )
        grouped.setdefault(key, []).append(row)

    summary: list[dict[str, Any]] = []
    for (trials_per_pair, propensity, effect_scale), rows in sorted(grouped.items()):
        item: dict[str, Any] = {
            "trials_per_pair": trials_per_pair,
            "propensity": propensity,
            "effect_scale": effect_scale,
            "repetitions": len(rows),
        }
        for metric in (
            "precision",
            "recall",
            "false_positives",
            "false_negatives",
            "mean_positive_edge_absolute_error",
        ):
            values = [float(row[metric]) for row in rows]
            item[f"{metric}_mean"] = mean(values)
            item[f"{metric}_sd"] = stdev(values) if len(values) > 1 else 0.0
        summary.append(item)

    return {
        "metadata": {
            "seed": seed,
            "repetitions": repetitions,
            "trials_per_pair_grid": list(trials_per_pair_grid),
            "propensities": list(propensities),
            "effect_scales": list(effect_scales),
            "minimum_discovery_effect": 0.05,
            "scope": (
                "randomized/ignorable trigger assignment with known propensities; "
                "no hidden-confounder identification claim"
            ),
        },
        "raw": raw,
        "summary": summary,
    }
