"""Publication-scale synthetic study plan for DynNav research gaps G1-G5.

This runner expands the CI mechanism checks across frozen parameter grids and
independent repetitions. It remains a synthetic study: ROS/Gazebo and hardware
evidence require separate execution protocols.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from dynnav.experiments.activation_threshold_frontier import (
    run_activation_threshold_frontier,
)
from dynnav.experiments.causal_graph_benchmark import (
    run_causal_graph_recovery_benchmark,
)
from dynnav.experiments.dependence_shift_benchmark import (
    run_dependence_shift_benchmark,
)
from dynnav.experiments.history_compression_benchmark import (
    run_history_compression_scaling,
)
from dynnav.experiments.noisy_activation_benchmark import ActivationObservationScenario
from dynnav.experiments.online_calibration_benchmark import (
    run_online_calibration_benchmark,
)


def run_full_research_gap_study(
    *,
    trials_per_condition: int = 2_000,
    repetitions: int = 5,
    seed: int = 20260925,
) -> dict[str, object]:
    """Run frozen synthetic parameter sweeps for all five research tracks."""

    if trials_per_condition <= 0:
        raise ValueError("trials_per_condition must be positive")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")

    g1: list[dict[str, object]] = []
    for repetition in range(repetitions):
        rows = run_dependence_shift_benchmark(
            trials=trials_per_condition,
            seed=seed + 1000 + repetition,
        )
        for row in rows:
            item = asdict(row)
            item["repetition"] = repetition
            g1.append(item)

    g2: list[dict[str, object]] = []
    sensor_profiles = (
        ("strong_calibrated", 0.95, 0.95, 0.95, 0.95),
        ("weak_calibrated", 0.65, 0.65, 0.65, 0.65),
        ("sensitivity_miscalibrated", 0.60, 0.90, 0.95, 0.90),
    )
    thresholds = (0.05, 0.10, 0.20, 0.30, 0.40, 0.50)
    scenario_index = 0
    for activation_probability in (0.2, 0.5, 0.8):
        for closure_probability in (0.2, 0.5, 0.8):
            for (
                profile_name,
                true_sensitivity,
                true_specificity,
                assumed_sensitivity,
                assumed_specificity,
            ) in sensor_profiles:
                for repetition in range(repetitions):
                    scenario = ActivationObservationScenario(
                        name=(
                            f"{profile_name}_q{activation_probability:.1f}"
                            f"_p{closure_probability:.1f}"
                        ),
                        activation_probability=activation_probability,
                        closure_probability=closure_probability,
                        true_sensitivity=true_sensitivity,
                        true_specificity=true_specificity,
                        assumed_sensitivity=assumed_sensitivity,
                        assumed_specificity=assumed_specificity,
                    )
                    rows = run_activation_threshold_frontier(
                        scenario,
                        thresholds=thresholds,
                        trials=trials_per_condition,
                        seed=seed + 2000 + scenario_index * 97 + repetition,
                    )
                    for row in rows:
                        item = asdict(row)
                        item["repetition"] = repetition
                        item["sensor_profile"] = profile_name
                        item["activation_probability"] = activation_probability
                        item["closure_probability"] = closure_probability
                        g2.append(item)
                scenario_index += 1

    g3: list[dict[str, object]] = []
    for true_probability in (0.1, 0.3, 0.5, 0.7, 0.9):
        for minimum_return in (0.5, 0.7, 0.9):
            for repetition in range(repetitions):
                rows = run_online_calibration_benchmark(
                    opportunities=trials_per_condition,
                    true_closure_probability=true_probability,
                    minimum_return_probability=minimum_return,
                    seed=seed
                    + 3000
                    + int(true_probability * 100) * 17
                    + int(minimum_return * 100)
                    + repetition,
                )
                for row in rows:
                    item = asdict(row)
                    item["repetition"] = repetition
                    item["true_closure_probability"] = true_probability
                    item["minimum_return_probability"] = minimum_return
                    g3.append(item)

    g4: list[dict[str, object]] = []
    for trials_per_pair in (250, 500, 1000, 2000):
        for repetition in range(repetitions):
            summary = run_causal_graph_recovery_benchmark(
                trials_per_pair=trials_per_pair,
                seed=seed + 4000 + trials_per_pair * 3 + repetition,
            )
            item = asdict(summary)
            item["repetition"] = repetition
            g4.append(item)

    g5 = [
        asdict(record)
        for record in run_history_compression_scaling(
            module_counts=(1, 2, 3, 4, 5, 6, 7, 8)
        )
    ]

    return {
        "metadata": {
            "seed": seed,
            "repetitions": repetitions,
            "trials_per_condition": trials_per_condition,
            "scope": "synthetic frozen G1-G5 study; not ROS/Gazebo or hardware efficacy",
        },
        "G1_dependence_shift_repetitions": g1,
        "G2_activation_grid": g2,
        "G3_online_learning_grid": g3,
        "G4_graph_recovery_grid": g4,
        "G5_search_scaling": g5,
    }


def write_full_study(
    result: dict[str, object],
    output_path: str | Path,
) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
