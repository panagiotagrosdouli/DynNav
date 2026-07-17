from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs/contributions/registry.yaml"


def test_generator_runs_and_emits_required_artifacts() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_contribution_programme_artifacts.py")],
        cwd=ROOT,
        check=True,
    )
    required = [
        ROOT / "docs/CONTRIBUTION_INDEX.md",
        ROOT / "docs/CONTRIBUTION_DEPENDENCY_GRAPH.md",
        ROOT / "docs/CONTRIBUTION_MATURITY_MATRIX.md",
        ROOT / "results/manifests/contribution_inventory.json",
        ROOT / "results/manifests/contribution_inventory.csv",
        ROOT / "results/manifests/contribution_dependency_graph.json",
        ROOT / "results/manifests/contribution_validation.json",
    ]
    assert all(path.is_file() and path.stat().st_size > 0 for path in required)


def test_generated_inventory_matches_registry() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    inventory_path = ROOT / "results/manifests/contribution_inventory.json"
    if not inventory_path.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/generate_contribution_programme_artifacts.py")],
            cwd=ROOT,
            check=True,
        )
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    registry_ids = [item["id"] for item in registry["contributions"]]
    inventory_ids = [item["id"] for item in inventory["contributions"]]
    assert inventory_ids == registry_ids == [f"C{i:02d}" for i in range(1, 27)]


def test_dependency_manifest_has_only_registered_nodes() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    registered = {item["id"] for item in registry["contributions"]}
    graph_path = ROOT / "results/manifests/contribution_dependency_graph.json"
    if not graph_path.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/generate_contribution_programme_artifacts.py")],
            cwd=ROOT,
            check=True,
        )
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    assert set(graph["nodes"]) == registered
    assert graph["edges"]
    assert all(edge["source"] in registered and edge["target"] in registered for edge in graph["edges"])
