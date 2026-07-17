from pathlib import Path

from scripts.validate_contribution_registry import load_registry, validate


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs/contributions/registry.yaml"


def test_registry_contains_exactly_c01_to_c26() -> None:
    entries = load_registry(REGISTRY)["contributions"]
    assert {entry["id"] for entry in entries} == {f"C{i:02d}" for i in range(1, 27)}


def test_registry_is_valid() -> None:
    report = validate(ROOT, REGISTRY)
    assert report["errors"] == [], report


def test_dependency_targets_are_registered() -> None:
    entries = load_registry(REGISTRY)["contributions"]
    ids = {entry["id"] for entry in entries}
    assert all(target in ids for entry in entries for target in entry.get("integrates_with", []))
