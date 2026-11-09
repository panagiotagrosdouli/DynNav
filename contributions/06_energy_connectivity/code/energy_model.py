# energy_model.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class EnergyParams:
    e0: float = 100.0              # initial energy budget
    move_cost: float = 1.0         # baseline energy per move
    turn_cost: float = 0.0         # optional (unused in 4-neigh grid)
    risk_energy_coeff: float = 0.0 # optional coupling: risky areas consume more energy
    compute_cost_per_expand: float = 0.0  # optional "compute load" modeling

    def __post_init__(self) -> None:
        values = {
            "e0": self.e0,
            "move_cost": self.move_cost,
            "turn_cost": self.turn_cost,
            "risk_energy_coeff": self.risk_energy_coeff,
            "compute_cost_per_expand": self.compute_cost_per_expand,
        }
        for name, value in values.items():
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")


class EnergyModel:
    def __init__(self, params: EnergyParams):
        self.p = params

    def step_energy_cost(self, risk: float) -> float:
        """
        Energy consumed for one action step.
        risk: scalar risk (0..1 typically) for the cell/transition
        """
        risk = float(risk)
        if not np.isfinite(risk) or risk < 0.0:
            raise ValueError("risk must be finite and nonnegative")
        return self.p.move_cost + self.p.risk_energy_coeff * risk
