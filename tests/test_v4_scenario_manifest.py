from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

from dynnav.experiments.v4_scenario_manifest import (
    V4_DEVELOPMENT_SEED,
    V4_HELDOUT_SEED,
    V4_VALIDATION_SEED,
    development_suite,
    generate_v4_suite,
    heldout_suite,
    scenario_from_dict,
    validation_suite,
)


def test_frozen_split_sizes_and_family_balance() -> None:
    expected = {
        "F1_bridge_detour",
        "F2_asymmetric_fork",
        "F3_redundant_loop",
        "F4_chamber_multitrigger",
        "F5_parallel_joint_cut",
        "F6_unavoidable_choice",
        "F7_multiple_safe_regions",
        "F8_null_control",
    }

    for suite, per_family in (
        (development_suite(), 6),
        (validation_suite(), 6),
        (heldout_suite(), 12),
    ):
        counts = Counter(item.family for item in suite)
        assert set(counts) == expected
        assert set(counts.values()) == {per_family}
        assert len({item.scenario_id for item in suite}) == len(suite)


def test_generator_is_deterministic_for_each_frozen_seed() -> None:
    assert development_suite() == generate_v4_suite(
        split="development",
        seed=V4_DEVELOPMENT_SEED,
        scenarios_per_family=6,
    )
    assert validation_suite() == generate_v4_suite(
        split="validation",
        seed=V4_VALIDATION_SEED,
        scenarios_per_family=6,
    )
    assert heldout_suite() == generate_v4_suite(
        split="heldout",
        seed=V4_HELDOUT_SEED,
        scenarios_per_family=12,
    )


def test_manifest_roundtrip_preserves_scenario_semantics() -> None:
    original = heldout_suite()[0]
    restored = scenario_from_dict(original.to_dict())

    assert restored == original
    restored.validate()


def test_specs_construct_execution_scenarios_without_sampling_outcomes() -> None:
    spec = validation_suite()[0]
    scenario = spec.to_execution_scenario(
        sensitivity=0.85,
        specificity=0.85,
    )

    assert scenario.name == spec.scenario_id
    assert scenario.arming_probabilities == tuple(
        hazard.arming_probability for hazard in spec.hazards
    )
    assert scenario.detection_sensitivities == (0.85,) * len(spec.hazards)
    assert scenario.detection_specificities == (0.85,) * len(spec.hazards)



def test_specs_can_separate_true_and_assumed_observation_models() -> None:
    spec = validation_suite()[0]
    assumed_q = tuple(
        min(1.0, hazard.arming_probability + 0.2)
        for hazard in spec.hazards
    )
    scenario = spec.to_execution_scenario(
        sensitivity=0.85,
        specificity=0.85,
        assumed_sensitivity=0.95,
        assumed_specificity=0.70,
        assumed_arming_probabilities=assumed_q,
    )

    assert scenario.detection_sensitivities == (0.85,) * len(spec.hazards)
    assert scenario.detection_specificities == (0.85,) * len(spec.hazards)
    assert scenario.planning_detection_sensitivities() == (
        (0.95,) * len(spec.hazards)
    )
    assert scenario.planning_detection_specificities() == (
        (0.70,) * len(spec.hazards)
    )
    assert scenario.planning_arming_probabilities() == assumed_q



def test_committed_v4_manifest_bytes_match_frozen_sha256s() -> None:
    root = Path("benchmarks/v4")
    expected: dict[str, str] = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        expected[Path(relative).name] = digest

    assert set(expected) == {
        "development.json",
        "validation.json",
        "heldout.json",
    }

    for name, digest in expected.items():
        observed = hashlib.sha256((root / name).read_bytes()).hexdigest()
        assert observed == digest
