"""Time-indexed predictive risk maps."""

from __future__ import annotations

from dataclasses import dataclass, field

from dynnav.planners.grid_map import GridCell


@dataclass(frozen=True)
class PredictiveRiskMap:
    """Risk field indexed by discrete future time.

    `risk_layers[t][cell]` stores the predicted risk at cell and future step t.
    Missing values fall back to `default_risk`.
    """

    width: int
    height: int
    horizon: int
    risk_layers: dict[int, dict[GridCell, float]] = field(default_factory=dict)
    default_risk: float = 0.0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if self.horizon < 0:
            raise ValueError("horizon must be non-negative")
        if not 0.0 <= self.default_risk <= 1.0:
            raise ValueError("default_risk must be in [0, 1]")
        for t, layer in self.risk_layers.items():
            if t < 0:
                raise ValueError(f"time index must be non-negative, got {t}")
            for cell, risk in layer.items():
                if not self.in_bounds(cell):
                    raise ValueError(f"risk cell outside map: {cell}")
                if not 0.0 <= risk <= 1.0:
                    raise ValueError(f"risk must be in [0, 1], got {risk!r}")

    def in_bounds(self, cell: GridCell) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def risk_at(self, cell: GridCell, time_step: int) -> float:
        """Return predicted risk at a cell and future time step."""
        if time_step < 0:
            raise ValueError("time_step must be non-negative")
        if not self.in_bounds(cell):
            return 1.0
        capped_time = min(time_step, self.horizon)
        return self.risk_layers.get(capped_time, {}).get(cell, self.default_risk)

    def max_risk_along(self, path: list[GridCell], start_time: int = 0) -> float:
        """Return maximum predicted risk along a timed path."""
        if not path:
            return 0.0
        return max(self.risk_at(cell, start_time + offset) for offset, cell in enumerate(path))

    def mean_risk_along(self, path: list[GridCell], start_time: int = 0) -> float:
        """Return mean predicted risk along a timed path."""
        if not path:
            return 0.0
        values = [self.risk_at(cell, start_time + offset) for offset, cell in enumerate(path)]
        return sum(values) / len(values)

    def with_risk(self, cell: GridCell, time_step: int, risk: float) -> "PredictiveRiskMap":
        """Return a new map with one risk value updated."""
        if time_step < 0:
            raise ValueError("time_step must be non-negative")
        if not self.in_bounds(cell):
            raise ValueError(f"cell outside map: {cell}")
        if not 0.0 <= risk <= 1.0:
            raise ValueError("risk must be in [0, 1]")
        layers = {t: dict(layer) for t, layer in self.risk_layers.items()}
        layers.setdefault(time_step, {})[cell] = risk
        return PredictiveRiskMap(
            width=self.width,
            height=self.height,
            horizon=max(self.horizon, time_step),
            risk_layers=layers,
            default_risk=self.default_risk,
        )
