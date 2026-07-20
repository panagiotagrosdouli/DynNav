from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_REGISTRY = ROOT / "configs/contributions/registry.yaml"
DASHBOARD_REGISTRY = ROOT / "src/dynnav_dashboard/contribution_registry.yaml"


def _load(path: Path) -> list[dict[str, object]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = payload.get("contributions", [])
    assert isinstance(rows, list)
    return rows


def test_dashboard_registry_covers_canonical_contributions_in_order() -> None:
    canonical = _load(CANONICAL_REGISTRY)
    dashboard = _load(DASHBOARD_REGISTRY)

    canonical_ids = [row["id"] for row in canonical]
    dashboard_ids = [row["id"] for row in dashboard]

    assert canonical_ids == dashboard_ids == [f"C{i:02d}" for i in range(1, 27)]


def test_dashboard_maturity_matches_canonical_registry() -> None:
    canonical = {row["id"]: row for row in _load(CANONICAL_REGISTRY)}
    dashboard = {row["id"]: row for row in _load(DASHBOARD_REGISTRY)}

    assert dashboard.keys() == canonical.keys()
    for contribution_id, canonical_row in canonical.items():
        assert dashboard[contribution_id]["maturity"] == canonical_row["status"]


def test_dashboard_renderers_are_unique_and_declared() -> None:
    dashboard = _load(DASHBOARD_REGISTRY)
    renderers = [row.get("renderer") for row in dashboard]

    assert all(isinstance(renderer, str) and renderer for renderer in renderers)
    assert len(renderers) == len(set(renderers)) == 26
