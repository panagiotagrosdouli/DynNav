from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Any

import yaml


@dataclass(frozen=True)
class ContributionMetadata:
    id: str
    title: str
    category: str
    summary: str
    renderer: str
    maturity: str


def load_contribution_registry() -> list[ContributionMetadata]:
    registry_path = files("dynnav_dashboard").joinpath("contribution_registry.yaml")
    payload: dict[str, Any] = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    rows = payload.get("contributions", [])
    contributions = [ContributionMetadata(**row) for row in rows]
    ids = [item.id for item in contributions]
    if len(contributions) != 26 or ids != [f"C{i:02d}" for i in range(1, 27)]:
        raise ValueError("Contribution registry must contain ordered entries C01 through C26")
    return contributions


def contribution_by_id(contribution_id: str) -> ContributionMetadata:
    for item in load_contribution_registry():
        if item.id == contribution_id:
            return item
    raise KeyError(contribution_id)
