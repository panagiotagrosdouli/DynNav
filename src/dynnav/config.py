"""Configuration loading for deterministic DynNav experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class DynNavConfig:
    """Runtime configuration for planning and benchmarking."""

    seed: int = 0
    width: int = 48
    height: int = 48
    obstacle_density: float = 0.18
    unknown_fraction: float = 0.25
    risk_weight: float = 4.0
    cvar_alpha: float = 0.9
    returnability_weight: float = 1.5
    max_expansions: int = 10000
    n_scenarios: int = 20

    @classmethod
    def from_yaml(cls, path: str | Path) -> "DynNavConfig":
        """Load configuration from a YAML file."""
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(**{key: value for key, value in data.items() if key in cls.__annotations__})

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable dictionary representation."""
        return {field: getattr(self, field) for field in self.__annotations__}
