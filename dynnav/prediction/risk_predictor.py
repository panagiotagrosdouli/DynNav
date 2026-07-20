"""Risk prediction models for future occupancy hazards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from dynnav.planners.grid_map import GridCell, GridMap
from dynnav.prediction.predictive_risk_map import PredictiveRiskMap


@dataclass(frozen=True)
class MovingRiskSource:
    """Simple moving risk source with constant velocity."""

    position: GridCell
    velocity: tuple[int, int]
    risk: float = 0.9
    radius: int = 0

    def validate(self) -> None:
        if not 0.0 <= self.risk <= 1.0:
            raise ValueError("risk must be in [0, 1]")
        if self.radius < 0:
            raise ValueError("radius must be non-negative")


class RiskPredictor(Protocol):
    """Interface for producing a future risk map."""

    def predict(self, grid: GridMap, horizon: int) -> PredictiveRiskMap:
        """Predict risk layers for the next `horizon` steps."""


@dataclass(frozen=True)
class StaticRiskPredictor:
    """Baseline predictor that repeats the current risk map across time."""

    def predict(self, grid: GridMap, horizon: int) -> PredictiveRiskMap:
        if horizon < 0:
            raise ValueError("horizon must be non-negative")
        layers = {t: dict(grid.risk) for t in range(horizon + 1)}
        return PredictiveRiskMap(width=grid.width, height=grid.height, horizon=horizon, risk_layers=layers)


@dataclass(frozen=True)
class ConstantVelocityRiskPredictor:
    """Predict future risk from constant-velocity moving sources."""

    sources: tuple[MovingRiskSource, ...]
    background_predictor: StaticRiskPredictor = StaticRiskPredictor()

    def predict(self, grid: GridMap, horizon: int) -> PredictiveRiskMap:
        if horizon < 0:
            raise ValueError("horizon must be non-negative")
        for source in self.sources:
            source.validate()

        base = self.background_predictor.predict(grid, horizon)
        layers = {t: dict(base.risk_layers.get(t, {})) for t in range(horizon + 1)}

        for t in range(horizon + 1):
            for source in self.sources:
                cx = source.position[0] + source.velocity[0] * t
                cy = source.position[1] + source.velocity[1] * t
                for dx in range(-source.radius, source.radius + 1):
                    for dy in range(-source.radius, source.radius + 1):
                        if abs(dx) + abs(dy) > source.radius:
                            continue
                        cell = (cx + dx, cy + dy)
                        if grid.in_bounds(cell):
                            layers[t][cell] = max(layers[t].get(cell, 0.0), source.risk)

        return PredictiveRiskMap(width=grid.width, height=grid.height, horizon=horizon, risk_layers=layers)
