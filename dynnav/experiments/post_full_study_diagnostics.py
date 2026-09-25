"""Post-full-study exploratory diagnostics for G3 and G5.

These diagnostics were designed after inspecting the frozen V1 full-study
artifact. They must not be mixed with the confirmatory V1 claim gate.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from dynnav.experiments.history_compression_state_space import (
    run_reachable_state_space_scaling,
)
from dynnav.experiments.safe_learning_lockout_benchmark import (
    run_safe_learning_lockout_benchmark,
)


def run_post_full_study_diagnostics(
    *,
    opportunities: int = 2_000,
    seed: int = 20260925,
) -> dict[str, object]:
    """Run the frozen exploratory G3 lockout and G5 state-space sweeps."""

    if opportunities <= 0:
        raise ValueError("opportunities must be positive")

    g3: list[dict[str, object]] = []
    condition = 0
    for true_probability in (0.1, 0.3, 0.5, 0.7, 0.9):
        for minimum_return in (0.5, 0.7, 0.9):
            for confidence in (0.80, 0.90, 0.95):
                rows = run_safe_learning_lockout_benchmark(
                    opportunities=opportunities,
                    true_closure_probability=true_probability,
                    minimum_return_probability=minimum_return,
                    confidence=confidence,
                    seed=seed + 100 + condition,
                )
                g3.extend(asdict(row) for row in rows)
                condition += 1

    g5 = [
        asdict(row)
        for row in run_reachable_state_space_scaling(
            module_counts=(1, 2, 3, 4, 5, 6)
        )
    ]

    return {
        "metadata": {
            "seed": seed,
            "opportunities_per_g3_condition": opportunities,
            "scope": (
                "post-full-study exploratory diagnostics; "
                "not part of frozen EXPERIMENT_PROTOCOL_G1_G5_V1"
            ),
        },
        "G3_safe_learning_lockout": g3,
        "G5_full_reachable_state_space": g5,
    }


def write_post_full_study_diagnostics(
    result: dict[str, object],
    output_path: str | Path,
) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
