from __future__ import annotations

from collections import Counter

from dynnav.experiments.v4_scenario_generator import (
    FAMILIES,
    HELDOUT_SEED,
    generate_v4_specs,
    heldout_v4_specs,
    manifest_payload,
    spec_to_scenario,
)


def test_heldout_generator_is_deterministic_and_has_96_scenarios() -> None:
    first = heldout_v4_specs()
    second = generate_v4_specs(seed=HELDOUT_SEED, scenarios_per_family=12)

    assert first == second
    assert len(first) == 96
    assert Counter(spec.topology_family for spec in first) == {
        family: 12 for family in FAMILIES
    }


def test_every_spec_materializes_to_a_valid_v4_execution_scenario() -> None:
    for spec in heldout_v4_specs():
        scenario = spec_to_scenario(spec, sensitivity=0.85, specificity=0.85)
        scenario.validate()
        assert scenario.start != scenario.goal
        assert scenario.safe_cells
        assert len(scenario.arming_probabilities) == len(scenario.hazard_model.closures)


def test_manifest_digest_is_stable_and_sensitive_to_scenario_payload() -> None:
    specs = heldout_v4_specs()
    first = manifest_payload(specs, split="heldout", generator_seed=HELDOUT_SEED)
    second = manifest_payload(specs, split="heldout", generator_seed=HELDOUT_SEED)

    assert first["scenario_payload_sha256"] == second["scenario_payload_sha256"]
    assert len(str(first["scenario_payload_sha256"])) == 64

    altered = list(specs)
    altered[0] = altered[0].__class__(
        **{
            **altered[0].__dict__,
            "arming_probabilities": tuple(
                0.4 if value != 0.4 else 0.7
                for value in altered[0].arming_probabilities
            ),
        }
    )
    changed = manifest_payload(
        tuple(altered),
        split="heldout",
        generator_seed=HELDOUT_SEED,
    )
    assert changed["scenario_payload_sha256"] != first["scenario_payload_sha256"]


def test_history_irrelevant_family_contains_explicit_null_controls() -> None:
    controls = [
        spec for spec in heldout_v4_specs()
        if spec.topology_family == "history_irrelevant"
    ]
    assert controls
    assert any(
        any(float(h["closure_probability"]) == 0.0 for h in spec.hazards)
        or any(q == 0.0 for q in spec.arming_probabilities)
        for spec in controls
    )
