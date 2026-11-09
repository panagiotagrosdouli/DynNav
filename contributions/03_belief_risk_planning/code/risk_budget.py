from dataclasses import dataclass
import math

@dataclass
class RiskBudgetTracker:
    """Tracks remaining risk budget (sum-risk model)."""
    B_total: float
    B_remaining: float | None = None
    spent: float = 0.0

    def __post_init__(self):
        self.reset(self.B_total)

    def reset(self, B_total: float):
        B_total = float(B_total)
        if not math.isfinite(B_total) or B_total < 0.0:
            raise ValueError("total risk budget must be finite and nonnegative")
        self.B_total = B_total
        self.B_remaining = float(B_total)
        self.spent = 0.0

    def consume(self, step_risk: float):
        r = float(step_risk)
        if not math.isfinite(r) or r < 0.0:
            raise ValueError("step risk must be finite and nonnegative")
        self.spent += r
        self.B_remaining -= r

    def will_violate(self, add_risk: float) -> bool:
        add_risk = float(add_risk)
        if not math.isfinite(add_risk) or add_risk < 0.0:
            raise ValueError("additional risk must be finite and nonnegative")
        return (self.B_remaining - add_risk) < 0.0

    def remaining(self) -> float:
        return float(self.B_remaining)

