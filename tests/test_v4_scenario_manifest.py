from __future__ import annotations

from collections import Counter

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
