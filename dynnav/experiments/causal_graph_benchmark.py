"""Synthetic interventional graph-recovery benchmark for trigger effects."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dynnav.causal_trigger_discovery import (
    TriggerOutcomeRecord,
    discover_trigger_closure_edges,
)


@dataclass(frozen=True)
class CausalGraphRecoverySummary:
    trials_per_pair: int
    injected_positive_edges: int
    discovered_edges: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float


def run_causal_graph_recovery_benchmark(
    *,
    trials_per_pair: int = 2_000,
    seed: int = 0,
    minimum_effect: float = 0.15,
) -> CausalGraphRecoverySummary:
    """Recover a frozen sparse trigger-to-closure graph from randomized trials."""

    if trials_per_pair <= 0:
        raise ValueError("trials_per_pair must be positive")
    rng = random.Random(seed)
    trigger_ids = ("t0", "t1", "t2")
    closure_ids = ("c0", "c1", "c2")
    effects = {
        ("t0", "c0"): 0.55,
        ("t1", "c2"): 0.35,
        ("t2", "c1"): 0.25,
    }
    baseline = 0.10
    records: list[TriggerOutcomeRecord] = []

    for trigger_id in trigger_ids:
        for closure_id in closure_ids:
            effect = effects.get((trigger_id, closure_id), 0.0)
            for _ in range(trials_per_pair):
                propensity = 0.5
                executed = rng.random() < propensity
                probability = baseline + effect * float(executed)
                records.append(
                    TriggerOutcomeRecord(
                        trigger_id=trigger_id,
                        closure_id=closure_id,
                        executed=executed,
                        closure_observed=rng.random() < probability,
                        execution_propensity=propensity,
                    )
                )

    estimates = discover_trigger_closure_edges(
        records,
        minimum_effect=minimum_effect,
        require_positive_95_interval=True,
    )
    discovered = {(estimate.trigger_id, estimate.closure_id) for estimate in estimates}
    truth = set(effects)
    true_positives = len(discovered & truth)
    false_positives = len(discovered - truth)
    false_negatives = len(truth - discovered)
    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    return CausalGraphRecoverySummary(
        trials_per_pair=trials_per_pair,
        injected_positive_edges=len(truth),
        discovered_edges=len(discovered),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
    )
